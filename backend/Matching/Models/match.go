package Models

type Candidate struct {
	UserID             uint64
	DistanceKM, Rating float64
	CompletedJobs      int
	SkillMatch         bool
	Verified           bool
	Score              float64
}
type Request struct {
	Latitude, Longitude float64
	RadiusKM            float64
	RequiredServiceID   uint64
	MinimumRating       float64
}
