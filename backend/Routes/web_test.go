package Routes

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/alumasinde/jijenge/Core/Config"
	"github.com/alumasinde/jijenge/Core/Logger"
)

func TestHealthAndReady(t *testing.T) {
	cfg := Config.Load()
	handler := Register(cfg, Logger.New("test"))

	for _, path := range []string{"/health", "/ready"} {
		req := httptest.NewRequest(http.MethodGet, path, nil)
		req.RemoteAddr = "127.0.0.1:" + path[1:]
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("%s: expected 200, got %d", path, rec.Code)
		}
		if !strings.Contains(rec.Body.String(), `"success":true`) {
			t.Fatalf("%s: unexpected body %s", path, rec.Body.String())
		}
		if rec.Header().Get("X-Content-Type-Options") != "nosniff" {
			t.Fatalf("%s: security headers missing", path)
		}
	}
}
