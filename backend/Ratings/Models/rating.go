package Models

import "time"

type Rating struct {
	ID, AssignmentID, ReviewerUserID, RevieweeUserID uint64
	Score                                            int
	Comment, Status                                  string
	CreatedAt                                        time.Time
}
