import requests
import json
import time

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test if the API is running and accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code == 200:
            print("API is running and accessible")
            return True
        else:
            print("API is not responding correctly")
            return False
    except requests.exceptions.ConnectionError:
        print("Cannot connect to API. Make sure the server is running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"Error testing API connection: {e}")
        return False

def fetch_latest_patient():
    """Fetch the latest patient using the API endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/patients/latest")
        if response.status_code == 200:
            patient = response.json()
            print("Latest patient fetched successfully")
            return patient
        elif response.status_code == 404:
            print("No patients found in the database")
            return None
        else:
            print(f"Error fetching latest patient: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching latest patient: {e}")
        return None

def make_prediction():
    """Make a prediction using the API endpoint"""
    try:
        # Prepare the prediction request
        prediction_data = {
            "model_type": "nn"
        }
        
        # Make the prediction request
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=prediction_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Prediction completed successfully")
            return result
        else:
            error_detail = response.json() if response.content else "Unknown error"
            print(f"Prediction failed: {response.status_code}")
            print(f"Error details: {error_detail}")
            return None
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None

def display_results(patient, prediction_result):
    """Display the results in a formatted way"""
    print("\n" + "="*60)
    print("PREDICTION RESULTS")
    print("="*60)
    
    if patient:
        print(f"Patient Information:")
        print(f"   • Patient ID: {patient.get('patient_id', 'N/A')}")
        print(f"   • Age: {patient.get('age', 'N/A')}")
        print(f"   • Sex: {patient.get('sex', 'N/A')}")
        print(f"   • Blood Pressure: {patient.get('bp', 'N/A')}")
        print(f"   • Cholesterol: {patient.get('cholesterol', 'N/A')}")
        print(f"   • Na_to_K Ratio: {patient.get('na_to_k', 'N/A')}")
        print(f"   • Actual Drug: {patient.get('drug', 'N/A')}")
    
    if prediction_result:
        print(f"\nPrediction Details:")
        print(f"   • Database Used: {prediction_result.get('db_used', 'N/A')}")
        print(f"   • Model Type: {prediction_result.get('model_type', 'N/A')}")
        print(f"   • Predicted Drug: {prediction_result.get('prediction', 'N/A')}")
        print(f"   • Actual Drug: {prediction_result.get('actual', 'N/A')}")
        
        # Check if prediction matches actual
        predicted = prediction_result.get('prediction', '')
        actual = prediction_result.get('actual', '')
        if predicted and actual:
            if predicted == actual:
                print(f"   • Prediction is CORRECT!")
            else:
                print(f"   • Prediction is INCORRECT")
    
    print("="*60)

def main():
    """Main function to orchestrate the prediction process"""
    print("Starting Drug Prediction Pipeline")
    print("="*60)
    
    # Step 1: Test API connection
    print("\n1. Testing API connection...")
    if not test_api_connection():
        return
    
    # Step 2: Fetch latest patient
    print("\n2. Fetching latest patient...")
    patient = fetch_latest_patient()
    if not patient:
        print("Cannot proceed without patient data")
        return
    
    # Step 3: Make prediction
    print("\n3. Making prediction...")
    prediction_result = make_prediction()
    if not prediction_result:
        print("Prediction failed")
        return
    
    # Step 4: Display results
    print("\n4. Displaying results...")
    display_results(patient, prediction_result)
    
    print("\nPrediction pipeline completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your API server and try again.") 