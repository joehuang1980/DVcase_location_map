#!/usr/bin/env python3
"""
Test script for the database functionality
"""
from database_manager import DiseaseDataDatabase

def test_database():
    print("🧪 Testing Database Functionality\n")
    
    db = DiseaseDataDatabase()
    
    # Test 1: Get database stats
    print("📊 Database Statistics:")
    try:
        stats = db.get_database_stats()
        print(f"  - Total predictions: {stats['total_predictions']:,}")
        print(f"  - Total dates: {stats['total_dates']}")
        print(f"  - Total regions: {stats['total_regions']}")
        print(f"  - Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
    except Exception as e:
        print(f"  ❌ Error getting stats: {e}")
    
    print()
    
    # Test 2: Get available dates
    print("📅 Available Dates:")
    try:
        dates = db.get_available_dates()
        print(f"  - First 5 dates: {dates[:5]}")
        print(f"  - Last 5 dates: {dates[-5:]}")
    except Exception as e:
        print(f"  ❌ Error getting dates: {e}")
    
    print()
    
    # Test 3: Get data for specific date
    test_date = "2023-06-01"
    print(f"📍 Predictions for {test_date}:")
    try:
        predictions = db.get_predictions_by_date(test_date)
        print(f"  - Total regions: {len(predictions)}")
        if predictions:
            print(f"  - Sample region: {predictions[0][1]} ({predictions[0][2]})")
            print(f"  - Sample prediction: {predictions[0][3]:.4f}")
            print(f"  - Sample percentage: {predictions[0][4]:.2f}%")
    except Exception as e:
        print(f"  ❌ Error getting predictions: {e}")
    
    print()
    
    # Test 4: Get high-risk regions
    print(f"⚠️  High-Risk Regions for {test_date} (>10%):")
    try:
        high_risk = db.get_high_risk_regions(test_date, 10)
        print(f"  - High-risk regions: {len(high_risk)}")
        for region in high_risk[:3]:  # Show first 3
            print(f"  - {region[1]} ({region[0]}): {region[2]:.2f}%")
    except Exception as e:
        print(f"  ❌ Error getting high-risk regions: {e}")
    
    print()
    
    # Test 5: Get daily summary
    print(f"📈 Daily Summary for {test_date}:")
    try:
        summary = db.get_daily_summary(test_date)
        if summary:
            print(f"  - Total regions: {summary[1]}")
            print(f"  - Avg prediction: {summary[3]:.4f}")
            print(f"  - Max prediction: {summary[4]:.4f}")
            print(f"  - High-risk regions: {summary[6]}")
            print(f"  - Medium-risk regions: {summary[7]}")
            print(f"  - Low-risk regions: {summary[8]}")
        else:
            print("  - No summary data found")
    except Exception as e:
        print(f"  ❌ Error getting daily summary: {e}")
    
    print()
    
    # Test 6: Get region timeline
    test_region = "A6727-0001-00"
    print(f"📊 Timeline for region {test_region}:")
    try:
        timeline = db.get_predictions_by_region(test_region, "2023-06-01", "2023-06-07")
        print(f"  - Data points: {len(timeline)}")
        if timeline:
            for point in timeline[:3]:  # Show first 3
                print(f"  - {point[0]}: {point[1]:.4f} ({point[2]:.2f}%)")
    except Exception as e:
        print(f"  ❌ Error getting region timeline: {e}")
    
    print("\n✅ Database testing complete!")

if __name__ == "__main__":
    test_database()