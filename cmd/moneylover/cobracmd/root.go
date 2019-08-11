package cobracmd

import (
	"log"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var rootCmd = &cobra.Command{
	Use:   "moneylover",
	Short: "An unofficial client of moneylover.me",
	Run: func(cmd *cobra.Command, args []string) {
		cmd.Usage()
		os.Exit(1)
	},
}

func init() {
	cobra.OnInitialize(initConfig)
}

func initConfig() {
	home, err := os.UserHomeDir()
	if err != nil {
		log.Fatal("Can't find HOME dir:", err)
	}

	viper.AddConfigPath(home)
	viper.SetConfigName(".config/moneylover")

	if err := viper.ReadInConfig(); err != nil {
		log.Fatal("Can't read config:", err)
	}
}

// Execute is to be called by main.go
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		log.Fatal(err)
	}
}
