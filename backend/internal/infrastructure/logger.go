package infrastructure

import (
	"log/slog"
	"os"
	"time"
)

const (
	KeyAction = "action"
	KeyStatus = "status"
	KeyError  = "error"
)

const (
	StatusFailed = "failed"
)

func InitLogger() {
	opts := &slog.HandlerOptions{
		Level: slog.LevelInfo,
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			if a.Key == slog.TimeKey {
				t := a.Value.Time().Local()
				return slog.String(slog.TimeKey, t.Format(time.DateTime))
			}

			return a
		},
	}

	handler := slog.NewJSONHandler(os.Stdout, opts)
	logger := slog.New(handler)
	slog.SetDefault(logger)
}

func GetLogger(layer string) *slog.Logger {
	return slog.Default().With("layer", layer)
}
