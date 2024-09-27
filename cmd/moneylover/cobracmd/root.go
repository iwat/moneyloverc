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

var home string

func init() {
	var err error
	home, err = os.UserHomeDir()
	if err != nil {
		log.Fatal("Can't find HOME dir:", err)
	}
	cobra.OnInitialize(initConfig)
}

const configName = "moneylover"
const configType = "yaml"

func initConfig() {

	viper.SetConfigName(configName)
	viper.SetConfigType(configType)
	viper.AddConfigPath(home + "/.config")

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			log.Println("Can't read config:", err)
		} else {
			log.Fatal("Can't read config:", err)
		}
	}
}

// Execute is to be called by main.go
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		log.Fatal(err)
	}
}

func saveConfig() error {
	return viper.WriteConfigAs(home + "/.config/" + configName + "." + configType)
}
