package jijenge

import (
	"context"
	"net/http"
	"time"

	"github.com/alumasinde/jijenge/Core/Config"
	"github.com/alumasinde/jijenge/Core/Database"
	"github.com/alumasinde/jijenge/Core/Logger"
	"github.com/alumasinde/jijenge/Routes"
)

type App struct {
	Config *Config.Config
	Logger *Logger.Logger
	Router http.Handler
	DB     *Database.DB
}

func NewApp(cfg *Config.Config) *App {
	logger := Logger.New(cfg.Environment)
	app := &App{Config: cfg, Logger: logger}

	if cfg.Environment == "production" && cfg.DBDSN == "" {
		panic("DB_DSN is required in production")
	}

	// Local/unit environments may omit DB_DSN and use repository implementations
	// supplied by Routes. Production must provide a real DB.
	if cfg.DBDSN != "" {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		db, err := Database.Open(ctx, cfg.DBDriver, Database.Config{
			DSN: cfg.DBDSN, MaxOpenConns: cfg.DBMaxOpenConns, MaxIdleConns: cfg.DBMaxIdleConns,
			ConnMaxLifetime: cfg.DBConnMaxLifetime, ConnMaxIdleTime: cfg.DBConnMaxIdleTime,
		})
		if err != nil {
			panic(err)
		}
		app.DB = db
	}

	app.Router = Routes.Register(cfg, logger, app.DB)
	return app
}

func (a *App) Close() error {
	if a == nil || a.DB == nil {
		return nil
	}
	return a.DB.Close()
}
