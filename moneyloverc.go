package moneyloverc

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/pkg/errors"
)

// DebugPayload can be set to `true` to debug HTTP payloads.
var DebugPayload = false

const userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"

var clientPattern = regexp.MustCompile("client=(.+?)&")

// Client provides a way to communicate with moneylover.
type Client struct {
	jwtToken     string
	refreshToken string
	clientID     string
}

// Restore creates a Client by restoring from a working refresh token.
func Restore(refreshToken, clientID string) *Client {
	return &Client{"", refreshToken, clientID}
}

// Login creates a Client by logging into moneylover service.
func Login(email, password string) (*Client, error) {
	res := struct {
		Data struct {
			RequestToken string `json:"request_token"`
			LoginURL     string `json:"login_url"`
		}
	}{}
	err := postForm("https://web.moneylover.me/api/user/login-url", nil, nil, &res)
	if err != nil {
		return nil, err
	}

	body := map[string]string{
		"email":    email,
		"password": password,
	}
	headers := map[string]string{
		"Authorization": "Bearer " + res.Data.RequestToken,
		"Client":        clientPattern.FindStringSubmatch(res.Data.LoginURL)[1],
	}
	tokenRes := struct {
		Status  bool   `json:"status"`
		Code    string `json:"code"`
		Message string `json:"message"`

		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
	}{}
	if err = postJSON("https://oauth.moneylover.me/token", body, headers, &tokenRes); err != nil {
		return nil, errors.Wrap(err, "login.token")
	}
	return &Client{tokenRes.AccessToken, tokenRes.RefreshToken, headers["Client"]}, err
}

// Refresh renew the access token of the current client.
func (c *Client) Refresh() error {
	body := map[string]string{}
	headers := map[string]string{
		"Authorization": "Bearer " + c.refreshToken,
		"Client":        c.clientID,
	}
	tokenRes := struct {
		Succeed bool   `json:"status"`
		Code    string `json:"code"`
		Message string `json:"message"`

		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
	}{}
	err := postJSON("https://oauth.moneylover.me/refresh-token", body, headers, &tokenRes)
	if err != nil {
		return err
	}
	if !tokenRes.Succeed {
		return fmt.Errorf("%s: %s", tokenRes.Code, tokenRes.Message)
	}
	c.jwtToken = tokenRes.AccessToken
	if tokenRes.RefreshToken != "" {
		c.refreshToken = tokenRes.RefreshToken
	}
	return nil
}

// GetUserInfo retrieves UserInfo for the logged in user.
func (c Client) GetUserInfo() (UserInfo, error) {
	var res UserInfo
	err := c.postRequest("/user/info", nil, nil, &res)
	return res, err
}

// GetWallets retrieves a list of Wallet(s).
func (c Client) GetWallets() ([]Wallet, error) {
	var res []Wallet
	err := c.postRequest("/wallet/list", nil, nil, &res)
	return res, err
}

// GetCategories retrieves a list of Category(s) in the given wallet.
func (c Client) GetCategories(walletID string) ([]Category, error) {
	var res []Category
	body := url.Values{}
	body.Set("walletId", walletID)
	err := c.postRequest("/category/list", body, nil, &res)
	return res, err
}

// GetTransactions retrieves a list of Transaction(s).
func (c Client) GetTransactions(walletID string, startDate, endDate time.Time) ([]Transaction, error) {
	var res struct {
		Transactions []Transaction `json:"transactions"`
	}
	body := url.Values{}
	body.Set("walletId", walletID)
	body.Set("startDate", startDate.In(time.Local).Format("2006-01-02"))
	body.Set("endDate", endDate.In(time.Local).Format("2006-01-02"))
	err := c.postRequest("/transaction/list", body, nil, &res)
	return res.Transactions, err
}

// AddTransaction adds the given transaction.
func (c Client) AddTransaction(t TransactionInput) (map[string]interface{}, error) {
	var res map[string]interface{}
	body := url.Values{}
	body.Set("transInfo", encodeToString(t))
	err := c.postRequest("/transaction/add", body, nil, &res)
	return res, err
}

func (c Client) String() string {
	parts := strings.SplitN(c.jwtToken, ".", 3)
	return fmt.Sprintf("Client[%s]", parts[2])
}

func (c Client) postRequest(path string, body url.Values, headers map[string]string, output interface{}) error {
	if headers == nil {
		headers = make(map[string]string)
	}
	headers["Authorization"] = "AuthJWT " + c.jwtToken

	res := struct {
		Error   int    `json:"error"`
		Msg     string `json:"msg"`
		E       string `json:"e"`
		Message string `json:"message"`
		Data    interface{}
	}{Data: output}
	err := postForm("https://web.moneylover.me/api"+path, body, headers, &res)
	if err != nil {
		return err
	}

	if res.Error != 0 {
		return fmt.Errorf("Error %d, %s", res.Error, res.Msg)
	}
	if res.E != "" {
		return fmt.Errorf("Error %s, %s", res.E, res.Message)
	}

	return nil
}

func postJSON(targetURL string, data interface{}, headers map[string]string, out interface{}) error {
	body, err := json.Marshal(data)
	if err != nil {
		return errors.Wrap(err, "postJSON.marshal")
	}

	return requestJSON(targetURL, bytes.NewBuffer(body), headers, "application/json; charset=utf-8", out)
}

func postForm(targetURL string, data url.Values, headers map[string]string, out interface{}) error {
	if data == nil {
		data = url.Values{}
	}

	return requestJSON(targetURL, strings.NewReader(data.Encode()), headers, "application/x-www-form-urlencoded", out)
}

func requestJSON(targetURL string, body io.Reader, headers map[string]string, contentType string, out interface{}) error {
	req, err := http.NewRequest("POST", targetURL, body)
	req.Header.Set("Content-Type", contentType)
	req.Header.Set("User-Agent", userAgent)
	for k, v := range headers {
		req.Header.Add(k, v)
	}

	if DebugPayload {
		b, err := httputil.DumpRequestOut(req, true)
		fmt.Println(string(b), err)
	}

	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return errors.Wrap(err, "requestJSON.callHTTP")
	}

	defer res.Body.Close()

	if DebugPayload {
		b, err := httputil.DumpResponse(res, true)
		fmt.Println(string(b), err)
	}

	decoder := json.NewDecoder(res.Body)
	if err := decoder.Decode(out); err != nil {
		return errors.Wrap(err, "requestJSON.decode")
	}
	return nil
}

func encodeToString(o interface{}) string {
	b, err := json.Marshal(o)
	if err != nil {
		panic(err)
	}
	return string(b)
}

// UserInfo contains an information about the logged in user.
type UserInfo struct {
	ID          string   `json:"_id"`
	DeviceID    string   `json:"deviceId"`
	Email       string   `json:"email"`
	IconPackage []string `json:"icon_package"`
	Purchased   bool     `json:"purchased"`
	// client_setting:map[df:0 dr:0 ds:0 er:true fd:1 fdw:1 fmy:0 l:en ls:1.532528444185e+12 ol:false om:0 ps:0 sa:false sb:0 sc:false sd:true sl:false]
}

func (u UserInfo) String() string {
	return fmt.Sprintf("UserInfo[%s %s @ %s]", u.ID, u.Email, u.DeviceID)
}

// Wallet contains an information about wallet.
type Wallet struct {
	ID                      string `json:"_id"`
	Name                    string `json:"name"`
	CurrencyID              int    `json:"currency_id"`
	Owner                   string `json:"owner"`
	TransactionNotification bool   `json:"transaction_notification"`
	Archived                bool   `json:"archived"`
	AccountType             int    `json:"account_type"`
	ExcludeTotal            bool   `json:"exclude_total"`
	Icon                    string `json:"icon"`
	ListUser                []struct {
		ID   string `json:"_id"`
		Name string `json:"name"`
	} `json:"listUser"`
	UpdateAt time.Time           `json:"updateAt"`
	IsDelete bool                `json:"isDelete"`
	Balance  []map[string]string `json:"balance"`
}

func (w Wallet) String() string {
	if len(w.Balance) > 0 {
		return fmt.Sprintf("Wallet[%s %s cur:%d bal:%v]", w.ID, w.Name, w.CurrencyID, w.Balance)
	}
	return fmt.Sprintf("Wallet[%s %s cur:%d]", w.ID, w.Name, w.CurrencyID)
}

// CategoryType defines two types of categories, income or expense.
type CategoryType int

const (
	// CategoryTypeIncome is income.
	CategoryTypeIncome CategoryType = iota + 1

	// CategoryTypeExpense is expense.
	CategoryTypeExpense
)

func (t CategoryType) String() string {
	switch t {
	case CategoryTypeIncome:
		return "income"
	case CategoryTypeExpense:
		return "expense"
	default:
		panic("invalid category type " + strconv.Itoa(int(t)))
	}
}

// Campaign contains an information about an event.
type Campaign struct {
	ID          string    `json:"_id"`
	Name        string    `json:"name"`
	Icon        string    `json:"icon"`
	Type        int       `json:"type"`
	StartAmount int       `json:"start_amount"`
	GoalAmount  int       `json:"goal_amount"`
	Owner       string    `json:"owner"`
	EndDate     time.Time `json:"end_date"`
	LastEditBy  string    `json:"lastEditBy"`
	TokenDevice string    `json:"tokenDevice"`
	CurrencyID  int       `json:"currency_id"`
	IsPublic    bool      `json:"isPublic"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	IsDelete    bool      `json:"isDelete"`
	Status      bool      `json:"status"`
}

func (c Campaign) String() string {
	return fmt.Sprintf("Campaign[%s %s %v]", c.ID, c.Name, c.Type)
}

// Category contains an information about transaction category.
type Category struct {
	ID       string       `json:"_id"`
	Icon     string       `json:"icon"`
	Metadata string       `json:"metadata"`
	Name     string       `json:"name"`
	Type     CategoryType `json:"type"`
}

func (c Category) String() string {
	return fmt.Sprintf("Category[%s %s %v]", c.ID, c.Name, c.Type)
}

// Transaction is an income or an expense entry in moneylover.
type Transaction struct {
	ID            string     `json:"_id"`
	Note          string     `json:"note"`
	Account       *Wallet    `json:"account"`
	Category      *Category  `json:"category"`
	Amount        float64    `json:"amount"`
	Date          time.Time  `json:"displayDate"`
	Images        []string   `json:"images"`
	ExcludeReport bool       `json:"exclude_report"`
	Campaigns     []Campaign `json:"campaign"`
	With          []string   `json:"with"`
}

func (t Transaction) String() string {
	return fmt.Sprintf("Tx[%v %f %s %s]", t.Date, t.Amount, t.Category, t.Account)
}

// TransactionInput is an income or an expense entry to be posted to moneylover.
type TransactionInput struct {
	Note     string    `json:"note"`
	Account  string    `json:"account"`
	Category string    `json:"category"`
	Amount   float64   `json:"amount"`
	Date     time.Time `json:"displayDate"`
}

func (t TransactionInput) String() string {
	return fmt.Sprintf("Tx[%v %f %s %s]", t.Date, t.Amount, t.Category, t.Account)
}
