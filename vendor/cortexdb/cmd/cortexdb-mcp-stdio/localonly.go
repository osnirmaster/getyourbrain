package main

import "github.com/liliang-cn/cortexdb/v2/pkg/localonly"

// GetYourBrain: build autocontido. Runs before main, so no client can be
// built on the stock transport.
func init() { localonly.Install() }
