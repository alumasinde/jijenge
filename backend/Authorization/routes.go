package Authorization

import (
	"net/http"

	"github.com/alumasinde/jijenge/Authorization/Handlers"
)

func RegisterRoutes(mux *http.ServeMux, handler *Handlers.Handler) {
	mux.HandleFunc("POST /api/v1/authorization/roles", handler.CreateRole)
	mux.HandleFunc("POST /api/v1/authorization/permissions", handler.CreatePermission)
}
