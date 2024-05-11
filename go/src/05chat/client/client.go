package main

import (
	"fmt"
)

func mainMenu() {
	var option string
	for {

		fmt.Println("--------欢迎登录聊天系统--------")
		fmt.Println("\t1.登录聊天室")
		fmt.Println("\t2.注册用户")
		fmt.Println("\t3.退出系统")
		fmt.Println("\t请输入(1-3)")

		fmt.Scanln(&option)

		switch option {
		case "1":
			fmt.Println("\t登录聊天室")
			return
		case "2":
			fmt.Println("\t注册用户")
			return
		case "3":
			fmt.Println("\t退出系统")
			return
		default:
			fmt.Println("\t输入有误,请重新输入")
		}
	}
}

func main() {

	mainMenu()
}
