package Config

import "testing"

func TestDatabaseConfigLoads(t *testing.T) {
	t.Setenv("DB_DRIVER", "mysql")
	t.Setenv("DB_DSN", "user:pass@tcp(localhost:3306)/jijenge")
	c := Load()
	if c.DBDriver != "mysql" || c.DBDSN == "" || c.DBMaxOpenConns <= 0 {
		t.Fatalf("unexpected db config: %+v", c)
	}
}
