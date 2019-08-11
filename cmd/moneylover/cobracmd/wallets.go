package cobracmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/iwat/moneyloverc"
)

func init() {
	rootCmd.AddCommand(walletsCmd)
	walletsCmd.AddCommand(listWalletsCmd)
}

var walletsCmd = &cobra.Command{
	Use:   "wallets",
	Short: "Manage multiple wallets (under development)",
	Run: func(cmd *cobra.Command, args []string) {
		cmd.Usage()
		os.Exit(1)
	},
}

var listWalletsCmd = &cobra.Command{
	Use:   "ls",
	Short: "List all available wallets",
	RunE: func(cmd *cobra.Command, args []string) error {
		c := moneyloverc.Restore(viper.GetString("client.refreshToken"), viper.GetString("client.clientID"))

		if err := c.Refresh(); err != nil {
			return err
		}
		wallets, err := c.GetWallets()
		if err != nil {
			return err
		}
		writer := tabwriter.NewWriter(os.Stdout, 0, 0, 1, ' ', tabwriter.AlignRight)
		fmt.Fprintln(writer, "ID\tName\tCurrency\tBalance\tUpdated\t")
		for _, w := range wallets {
			for _, pair := range w.Balance {
				for cur, amt := range pair {
					fmt.Fprintf(writer, "%s\t%s\t%s\t%s\t%v\t\n", w.ID, w.Name, cur, amt, w.UpdateAt)
				}
			}
		}
		writer.Flush()
		return nil
	},
}
