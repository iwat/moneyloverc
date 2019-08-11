package cobracmd

import (
	"fmt"
	"os"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/iwat/moneyloverc"
)

func init() {
	rootCmd.AddCommand(txsCmd)
	txsCmd.AddCommand(listTxsCmd)

	listTxsCmd.Flags().String("wid", "", "Wallet ID")
}

var txsCmd = &cobra.Command{
	Use:   "txs",
	Short: "Manage transactions",
	Run: func(cmd *cobra.Command, args []string) {
		cmd.Usage()
		os.Exit(1)
	},
}

var listTxsCmd = &cobra.Command{
	Use:   "ls",
	Short: "List transactions",
	RunE: func(cmd *cobra.Command, args []string) error {
		widFlag := cmd.Flag("wid")
		if widFlag.Value.String() == "" {
			return fmt.Errorf("-wid [wallet ID] is required")
		}

		c := moneyloverc.Restore(viper.GetString("client.refreshToken"), viper.GetString("client.clientID"))

		if err := c.Refresh(); err != nil {
			return err
		}
		txs, err := c.GetTransactions(widFlag.Value.String(), time.Now().Add(-time.Hour*48), time.Now())
		if err != nil {
			return err
		}
		writer := tabwriter.NewWriter(os.Stdout, 0, 0, 1, ' ', tabwriter.AlignRight)
		fmt.Fprintln(writer, "ID\tDate\tAmount\tCategory\tNote\t")
		for _, tx := range txs {
			fmt.Fprintf(writer, "%s\t%s\t%.2f\t%s\t%s\t\n", tx.ID, tx.Date.Format("2006-01-02"), tx.Amount, tx.Category.Name, tx.Note)
		}
		writer.Flush()
		return nil
	},
}
