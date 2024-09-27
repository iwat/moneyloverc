package cobracmd

import (
	"fmt"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"golang.org/x/crypto/ssh/terminal"
	"syscall"

	"github.com/iwat/moneyloverc"
)

func init() {
	rootCmd.AddCommand(loginCmd)

	loginCmd.Flags().String("email", "", "Email address")
	if err := loginCmd.MarkFlagRequired("email"); err != nil {
		panic(err)
	}
}

var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "Login into MoneyLover",
	RunE: func(cmd *cobra.Command, args []string) error {
		email := cmd.Flag("email")
		fmt.Print("Password: ")
		pass, err := terminal.ReadPassword(syscall.Stdin)
		if err != nil {
			return fmt.Errorf("error reading password: %v", err)
		}

		client, err := moneyloverc.Login(email.Value.String(), string(pass))
		if err != nil {
			return fmt.Errorf("error logging in: %v", err)
		}
		err = client.Refresh()
		if err != nil {
			return fmt.Errorf("error refreshing token: %v", err)
		}

		_, err = client.GetWallets()
		if err != nil {
			return fmt.Errorf("error listing wallets: %v", err)
		}

		token, clientID := client.Export()
		viper.Set("client.refreshToken", token)
		viper.Set("client.clientID", clientID)
		return saveConfig()
	},
}
