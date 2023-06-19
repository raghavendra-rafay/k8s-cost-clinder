package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/pricing"
)

func main() {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String("us-east-1"), // Replace with your desired region
	})

	if err != nil {
		fmt.Println("Failed to create AWS session:", err)
		return
	}

	pricingSvc := pricing.New(sess)

	params := &pricing.GetProductsInput{
		ServiceCode: aws.String("AmazonEC2"),
		Filters: []*pricing.Filter{
			{
				Field: aws.String("operatingSystem"),
				Type:  aws.String("TERM_MATCH"),
				Value: aws.String("Linux"),
			},
		},
	}

	resp, err := pricingSvc.GetProducts(params)
	if err != nil {
		fmt.Println("Failed to retrieve instance types:", err)
		return
	}

	headers := []string{"InstanceType", "CPU", "Memory", "Cost"}

	file, err := os.Create("aws_data.csv")
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	// Create a CSV writer
	csvWriter := csv.NewWriter(file)
	csvWriter.Write(headers)

	csvRows := make([][]string, 0)

	for _, price := range resp.PriceList {
		//product := make(map[string]interface{})
		var priceDimension map[string]interface{}
		product := price["product"].(map[string]interface{})
		terms := price["terms"].(map[string]interface{})
		if terms["OnDemand"] == nil {
			fmt.Println("Not Ondemand", terms)
			continue
		}
		onDemand := terms["OnDemand"].(map[string]interface{})
		for _, val := range onDemand {
			priceDimension = val.(map[string]interface{})
		}

		attributes := product["attributes"].(map[string]interface{})

		//fmt.Println(attributes)
		if attributes["instanceType"] == nil {
			fmt.Println("Not instanceType", attributes)
			continue
		}
		instanceType := attributes["instanceType"].(string)

		cpu := attributes["vcpu"].(string)
		memory := attributes["memory"].(string)

		priceDimensions := priceDimension["priceDimensions"].(map[string]interface{})
		for _, pd := range priceDimensions {
			priceDimension := pd.(map[string]interface{})
			pricePerUnit := priceDimension["pricePerUnit"].(map[string]interface{})
			if pricePerUnit["USD"] == nil {
				fmt.Printf("Wrong instance type %s\n", instanceType)
				fmt.Println("Cost per Hour: ", pricePerUnit)
				fmt.Println("--------------------------------------------------")
			} else {
				cost := pricePerUnit["USD"].(string)

				fmt.Printf("Instance Type: %s\n", instanceType)
				fmt.Printf("CPU: %s\n", cpu)
				fmt.Printf("Memory: %s\n", memory)
				fmt.Printf("Cost per Hour: %s\n", cost)
				fmt.Println("--------------------------------------------------")
				var costF float64
				if costF, err = strconv.ParseFloat(cost, 64); err != nil {
					log.Fatal("Failed to convert cost string to float", "error", err.Error())
				}
				if costF == 0.0 {
					continue
				}
				if cpu == "NA" || memory == "NA" {
					continue
				}
				csvRow := []string{instanceType, cpu, memory, cost}
				csvRows = append(csvRows, csvRow)

			}
		}

	}

	for _, csvRow := range csvRows {
		err := csvWriter.Write(csvRow)
		if err != nil {
			log.Fatal("Failed to update csv", "error", err.Error())
		}
	}

	csvWriter.Flush()

	if err := csvWriter.Error(); err != nil {
		log.Fatal("Failed to flush csv writer", err)
	}

	// Save the file
	if err := file.Sync(); err != nil {
		log.Fatal("Failed to save file", err)
	}
}
