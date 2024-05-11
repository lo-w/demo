package main

import (
	// "crypto/md5"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
)

func main() {

	file := "/home/lo/.repo/work/py/bawang.mp4"

	f, err := os.Open(file)
	if err != nil {
		panic(err)
	}

	defer func() {
		_ = f.Close()
	}()

	buf := make([]byte, 1024*1024)
	h := sha256.New()

	for {
		bytesRead, err := f.Read(buf)
		if err != nil {
			if err != io.EOF {
				panic(err)
			}

			fmt.Println("EOF")
			break
		}

		fmt.Printf("bytes read: %d\n", bytesRead)
		h.Write(buf)
	}

	fmt.Printf("checksum: %s\n", hex.EncodeToString(h.Sum(nil)))

}
