package localonly

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestAllowed(t *testing.T) {
	for addr, want := range map[string]bool{
		"127.0.0.1:9200":     true,
		"[::1]:9200":         true,
		"localhost:11434":    true,
		"api.openai.com:443": false,
		"10.0.0.5:80":        false,
		"0.0.0.0:80":         false,
	} {
		if got := Allowed(addr); got != want {
			t.Errorf("Allowed(%q) = %v, want %v", addr, got, want)
		}
	}
}

func TestInstallBlocksExternalAndKeepsLoopback(t *testing.T) {
	Install()
	if _, err := http.Get("https://api.openai.com/v1/models"); err == nil {
		t.Fatal("external request was not blocked")
	}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {}))
	defer srv.Close()
	resp, err := http.Get(srv.URL)
	if err != nil {
		t.Fatalf("loopback request failed: %v", err)
	}
	resp.Body.Close()
}
