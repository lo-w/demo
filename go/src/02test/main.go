package main

import (
	"fmt"
	"math/rand"
	"sort"
)

type Hero struct {
	Name string
	Age  int
}

type HeroSlice []Hero

func (hs HeroSlice) Len() int {
	return len(hs)
}

func (hs HeroSlice) Less(i, j int) bool {
	return hs[i].Age < hs[j].Age
	// return true
}

func (hs HeroSlice) Swap(i, j int) {
	hs[i], hs[j] = hs[j], hs[i]
}

func main() {
	var heroes HeroSlice
	for i := 0; i < 10; i++ {
		hero := Hero{
			Name: fmt.Sprintf("hero~%d", rand.Intn(100)),
			Age:  rand.Intn(100),
		}
		heroes = append(heroes, hero)
	}

	fmt.Println("-------------before order-------------")
	for _, h := range heroes {
		fmt.Println(h)
	}

	sort.Sort(heroes)
	fmt.Println("-------------after  order-------------")
	for _, h := range heroes {
		fmt.Println(h)
	}

}
