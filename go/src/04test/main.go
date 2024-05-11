package main

import (
	"fmt"
)

// var sumMap = make(map[int]int, 10)

func calSum(n int, sumChan chan int) {
	sum := 0
	for i := 1; i < n+1; i++ {
		sum += i
	}
	sumChan <- sum
}

func main() {
	var sumChan = make(chan int, 10)

	n := 100
	for i := 1; i < n+1; i++ {
		go calSum(i, sumChan)
	}

	// for i := 0; i < len(sumMap); i++ {
	// 	var a = <-sumChan
	// 	fmt.Println(a)
	// }
	close(sumChan)
	for v := range sumChan {
		fmt.Println(v)
	}

}
