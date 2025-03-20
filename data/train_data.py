# Load and clean the datasets
def load_and_clean_data():
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder
    import pickle

    # Load training and testing datasets
    train_data = pd.read_csv('Training.csv')
    test_data = pd.read_csv('Testing.csv')

    # Drop unnecessary column
    if 'Unnamed: 133' in train_data.columns:
        train_data = train_data.drop(columns=['Unnamed: 133'])

    # Encode the target column
    le = LabelEncoder()
    train_data['prognosis'] = le.fit_transform(train_data['prognosis'])
    test_data['prognosis'] = le.transform(test_data['prognosis'])  # Use the same encoder

    # Save the disease mapping
    disease_mapping = {index: disease for index, disease in enumerate(le.classes_)}
    with open('disease_mapping.pkl', 'wb') as f:
        pickle.dump(disease_mapping, f)

    # Separate features and target
    X_train = train_data.drop(columns=['prognosis'])
    y_train = train_data['prognosis']
    X_test = test_data.drop(columns=['prognosis'])
    y_test = test_data['prognosis']

    return X_train, y_train, X_test, y_test, le


# Train the model and save it
def train_and_save_model(X_train, y_train, feature_names):
    from sklearn.ensemble import RandomForestClassifier
    import pickle

    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save the model
    with open('svc.pkl', 'wb') as f:
        pickle.dump(model, f)

    # Save the symptom list (feature names)
    with open('symptom_list.pkl', 'wb') as f:
        pickle.dump(feature_names, f)

    return model


# Evaluate the model
def evaluate_model(model, X_test, y_test):
    from sklearn.metrics import accuracy_score, classification_report

    # Predict and evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    return accuracy, report


# Main execution block
if __name__ == "__main__":
    import os

    # Load and clean data
    X_train, y_train, X_test, y_test, label_encoder = load_and_clean_data()

    # Train the model and save
    model = train_and_save_model(X_train, y_train, X_train.columns.tolist())

    # Evaluate the model
    accuracy, report = evaluate_model(model, X_test, y_test)

    # Output results
    print("Model Accuracy:", accuracy)
    print("Classification Report:\n", report)

    # Check if all files were generated
    files = ['svc.pkl', 'symptom_list.pkl', 'disease_mapping.pkl']
    for file in files:
        if os.path.exists(file):
            print(f"{file} generated successfully.")
        else:
            print(f"Error: {file} not found!")
