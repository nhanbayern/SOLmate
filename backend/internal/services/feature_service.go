package services

import (
	"backend/internal/infrastructure"
	"backend/internal/models"
	"context"
	"log/slog"
	"math"
	"time"
)

type FeatureService struct {
	log *slog.Logger
}

func NewFeatureService() *FeatureService {
	logger := infrastructure.GetLogger("FEATURE_SERVICE")

	return &FeatureService{
		log: logger,
	}
}

var IndustryRiskMapping = map[string]float64{
	"default":                                        0.6,
	"Accommodation_and_Food_Services":                0.8,
	"Agriculture_Forestry_Fishing":                   0.7,
	"Construction":                                   0.9,
	"Education":                                      0.3,
	"Entertainment_and_Recreation":                   0.7,
	"Finance_and_Insurance":                          0.4,
	"Health_Care_and_Social_Assistance":              0.4,
	"Information":                                    0.5,
	"Manufacturing":                                  0.6,
	"Mining_Quarrying_and_Oil_and_Gas_Extraction":    0.8,
	"Other_Services":                                 0.6,
	"Professional_Scientific_and_Technical_Services": 0.5,
	"Real_Estate_and_Rental_and_Leasing":             0.7,
	"Retail_Trade":                                   0.6,
	"Transportation_and_Warehousing":                 0.7,
	"Utilities":                                      0.4,
	"Wholesale_Trade":                                0.5,
	"FMCG":                                           0.5,
	"Textile_Garment_and_Footwear":                   0.7,
	"Wood_Processing":                                0.7,
	"Plastic_and_Rubber":                             0.6,
	"Mechanical_and_Engineering":                     0.6,
	"Electronics_and_Informatics":                    0.5,
	"Pharmaceuticals_and_Medical_Equipment":          0.4,
	"Energy":                                         0.5,
	"Telecommunications":                             0.4,
	"Media_and_Advertising":                          0.6,
	"Travel_and_Tourism":                             0.8,
	"Automotive":                                     0.6,
	"Logistics":                                      0.7,
	"E_commerce":                                     0.5,
	"Legal_and_Consulting":                           0.4,
	"Human_Resources":                                0.5,
	"Security_Services":                              0.6,
	"Environmental_Services":                         0.5,
	"Research_and_Development":                       0.4,
	"Non_profit_and_Social_Enterprises":              0.3,
	"Government_and_Public_Sector":                   0.2,
	"Arts_and_Culture":                               0.7,
	"Sports_and_Fitness":                             0.6,
	"Beauty_and_Personal_Care":                       0.6,
	"Home_and_Garden":                                0.5,
	"Pet_Services":                                   0.5,
	"Crafts_and_Hobbies":                             0.6,
	"Events_and_Weddings":                            0.7,
	"Printing_and_Publishing":                        0.6,
	"Chemicals":                                      0.7,
	"Jewelry_and_Gems":                               0.6,
	"Tobacco":                                        0.9,
	"Firearms_and_Weapons":                           0.9,
	"Gambling_and_Betting":                           1.0,
	"Adult_Entertainment":                            1.0,
	"Pawn_Shops":                                     0.8,
	"Scrap_Metal_and_Junk_Dealers":                   0.8,
	"Political_Organizations":                        0.7,
	"Nightclubs_and_Bars":                            0.8,
	"Unregulated_Financial_Services":                 1.0,
	"Cryptocurrency_Services":                        0.9,
	"Livestock_Trading":                              0.7,
}

var YearsInBusinessBins = []struct {
	MaxYears int
	Score    float64
}{
	{1, 0.2},
	{3, 0.4},
	{5, 0.6},
	{10, 0.8},
	{1000, 1.0},
}

func (s *FeatureService) CalculateFeatures(
	ctx context.Context,
	merchant *models.Merchant,
	txns []*models.TransactionLog,
) ([]float64, error) {
	s.log.Info(
		"Calculating features",
		"merchant_id", merchant.ID,
	)

	now := time.Now()
	thirtyDaysAgo := now.AddDate(0, 0, -30)
	ninetyDaysAgo := now.AddDate(0, 0, -90)
	oneEightyDaysAgo := now.AddDate(0, 0, -180)

	var rev30, rev90, rev90to180 float64
	var count90 int
	dailyRevenue := make(map[string]float64)
	monthlyRevenue := make(map[string]float64)

	for _, t := range txns {
		if t.TransactionTime.After(thirtyDaysAgo) {
			rev30 += t.Amount
		}

		if t.TransactionTime.After(ninetyDaysAgo) {
			rev90 += t.Amount
			count90++

			dayKey := t.TransactionTime.Format("2006-01-02")
			dailyRevenue[dayKey] += t.Amount

			monthKey := t.TransactionTime.Format("2006-01")
			monthlyRevenue[monthKey] += t.Amount
		} else if t.TransactionTime.After(oneEightyDaysAgo) {
			rev90to180 += t.Amount
		}
	}

	revMean30 := rev30 / 30
	revMean90 := rev90 / 90

	txnFreq := float64(count90) / 90

	growthValue := rev90 - rev90to180
	var growthRate float64
	if rev90to180 > 0 {
		growthRate = growthValue / rev90to180
	} else if rev90 > 0 {
		growthRate = 1.0
	}
	growthScore := clip((growthRate+1)/2, 0, 1)

	var cvValue float64
	if len(monthlyRevenue) > 1 {
		var sum, sumSq float64

		for _, v := range monthlyRevenue {
			sum += v
			sumSq += v * v
		}

		mean := sum / float64(len(monthlyRevenue))
		variance := (sumSq / float64(len(monthlyRevenue))) - (mean * mean)
		std := math.Sqrt(math.Max(0, variance))

		if mean > 0 {
			cvValue = std / mean
		}
	}
	cvScore := clip(1-cvValue, 0, 1)

	var spikeRatio float64 = 1.0
	if len(dailyRevenue) > 0 {
		var maxRev, sumRev float64

		for _, v := range dailyRevenue {
			if v > maxRev {
				maxRev = v
			}
			sumRev += v
		}

		meanRev := sumRev / 90
		if meanRev > 0 {
			spikeRatio = maxRev / meanRev
		}
	}
	spikeScore := clip(1-(spikeRatio/10), 0, 1)

	var txnFreqScore float64 = 0.2
	switch {
	case txnFreq >= 1:
		txnFreqScore = 1.0
	case txnFreq >= 0.5:
		txnFreqScore = 0.8
	case txnFreq >= 0.2:
		txnFreqScore = 0.5
	}

	yearsScore := 0.2
	for _, b := range YearsInBusinessBins {
		if merchant.YearsInBusiness <= b.MaxYears {
			yearsScore = b.Score
			break
		}
	}

	riskFactor, ok := IndustryRiskMapping[merchant.Industry]
	if !ok {
		riskFactor = IndustryRiskMapping["default"]
	}
	industryScore := clip(1-riskFactor, 0, 1)

	return []float64{
		revMean30,
		revMean90,
		txnFreq,
		growthValue,
		growthScore,
		cvValue,
		cvScore,
		spikeRatio,
		spikeScore,
		txnFreqScore,
		yearsScore,
		industryScore,
	}, nil
}

func clip(val, min, max float64) float64 {
	if val < min {
		return min
	}

	if val > max {
		return max
	}

	return val
}
