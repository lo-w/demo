package main

import (
	"fmt"
	"os"
	"time"

	"sync/atomic"

	"gopkg.in/ini.v1"
)

type Headers struct {
	// User-Agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
	// Accept "*/*",
	// "Accept-Encoding":"gzip, deflate, br",
	// "Accept-Language":"en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
	// "Cache-Control":"no-cache",
	// "Connection":"keep-alive",
	// "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
	// "Host":"ericsson.lightning.force.com",
	// "Origin":'https://ericsson.lightning.force.com',
	// "Pragma":"no-cache",
	// "Referer":"https://ericsson.lightning.force.com/lightning/o/Case/list?filterName=%s" % filter_name,
	// "Sec-Ch-Ua" '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
	// "Sec-Ch-Ua-Mobile":"?0",
	// "Sec-Ch-Ua-Platform":"Windows",
	// "Sec-Fetch-Dest":"empty",
	// "Sec-Fetch-Mode":"cors",
	// "Sec-Fetch-Site":"same-origin",
}

type Data struct {
}

type CFGI struct {
	cfg     *ini.Section
	headers *Headers
	data    *Data
}

var conf atomic.Value

func readConfig() (CFGI, error) {
	ci := CFGI{}
	cfg, err := ini.Load("ticket.ini")
	if err != nil {
		fmt.Printf("Fail to read file: %v", err)
		os.Exit(1)
	}
	cfg_default := cfg.Section("DEFAULT")
	// aura_context := cfg_default.Key("AURA_CONTEXT")
	// aura_token := cfg_default.Key("AURA_TOKEN")
	ci.cfg = cfg_default
	return ci, nil
}

func updateConfig() {
	for {
		newConfig, err := readConfig()
		if err != nil {
			fmt.Println("Error reading config:", err)
			time.Sleep(time.Second * 10)
			continue
		}
		conf.Store(newConfig)
		fmt.Println("Config updated")
		time.Sleep(time.Second * 10)
	}
}

func getCases() {
	for {
		curConfig := conf.Load().(CFGI)
		cfg_default := curConfig.cfg
		fmt.Println("Using config:")
		fmt.Println(cfg_default.Key("MAX_REFRESH"))
		fmt.Println(cfg_default.Key("MIN_REFRESH"))
		fmt.Println(cfg_default.Key("ASSIGN_QUEUE"))
		// fmt.Println(currentConfig)
		time.Sleep(time.Second * 3)
	}
}

func filterCases() {

}

func assignCase() {

}

func main() {

	initialConfig, err := readConfig()
	if err != nil {
		fmt.Println("Error reading initial config:", err)
		return
	}
	conf.Store(initialConfig)
	go updateConfig()
	go getCases()
	go filterCases()
	go assignCase()

	select {}
}
