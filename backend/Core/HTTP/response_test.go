package HTTP

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestJSONResponse(t *testing.T) {
	rec := httptest.NewRecorder()
	JSON(rec, http.StatusOK, map[string]string{"status": "ok"})

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}
	if !strings.Contains(rec.Header().Get("Content-Type"), "application/json") {
		t.Fatal("expected JSON content type")
	}
	if !strings.Contains(rec.Body.String(), `"success":true`) {
		t.Fatalf("unexpected response: %s", rec.Body.String())
	}
}
