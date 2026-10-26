// Package localonly is the GetYourBrain egress guard: every outbound
// connection this binary opens must go to the loopback interface.
//
// GetYourBrain builds CortexDB as a self-contained component. The upstream
// code can talk to external embedders, LLMs, rerankers (OPENAI_API_KEY and
// friends are read from the environment), remote brains over gRPC and SPARQL
// SERVICE endpoints. Instead of patching each client, Install swaps the
// transport they all share, and Dial is the only dialer gRPC gets.
package localonly

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"
)

// Allowed reports whether addr ("host:port") names the loopback interface.
// Hostnames other than "localhost" are refused before any DNS lookup, so not
// even the name leaves the machine.
func Allowed(addr string) bool {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		host = addr
	}
	if host == "localhost" {
		return true
	}
	ip := net.ParseIP(host)
	return ip != nil && ip.IsLoopback()
}

// Dial is a net.Dialer.DialContext that refuses anything but loopback.
func Dial(ctx context.Context, network, addr string) (net.Conn, error) {
	if !Allowed(addr) {
		return nil, fmt.Errorf("conexão com %s bloqueada: GetYourBrain só permite loopback", addr)
	}
	d := net.Dialer{Timeout: 30 * time.Second}
	return d.DialContext(ctx, network, addr)
}

// Install points http.DefaultTransport (and so http.DefaultClient and every
// http.Client without its own Transport) at Dial, with proxies disabled.
func Install() {
	t := http.DefaultTransport.(*http.Transport).Clone()
	t.Proxy = nil
	t.DialContext = Dial
	t.DialTLSContext = nil
	http.DefaultTransport = t
}
