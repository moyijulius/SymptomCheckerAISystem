# Import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, learning_curve
from sklearn.inspection import permutation_importance
import pickle
import os
from collections import Counter

# Set style for plots
plt.style.use('fivethirtyeight')
sns.set_palette('bright')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Load and clean the datasets
def load_and_clean_data():
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder
    import pickle

    # Load training and testing datasets
    train_data = pd.read_csv('Training.csv')
    test_data = pd.read_csv('Testing.csv')

        
    # Examine data structure
    #examine training data
    print("\n--- TRAINING DATA OVERVIEW ---")
    print(f"Shape: {train_data.shape}")
    print("\nFirst 5 rows:")
    print(train_data.head())
    print("\nData types:")
    print(train_data.dtypes)
    print("\nMissing values:")
    print(train_data.isnull().sum())
    print("\nSummary statistics:")
    print(train_data.describe())
    # Examine Testing data
    print("\n--- TESTING DATA OVERVIEW ---")
    print(f"Shape: {test_data.shape}")
    print("\nFirst 5 rows:")
    print(test_data.head())
    print("\nData types:")
    print(test_data.dtypes)
    print("\nMissing values:")
    print(test_data.isnull().sum())


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

    return X_train, y_train, X_test, y_test, le, disease_mapping


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

    return accuracy, report, y_pred


# Function to analyze class distribution
def analyze_class_distribution(y_train, y_test, disease_mapping):
    # Count occurrences of each class
    train_counts = Counter(y_train)
    test_counts = Counter(y_test)
    
    # Convert to DataFrames
    train_df = pd.DataFrame({
        'disease': [disease_mapping[i] for i in train_counts.keys()],
        'count': list(train_counts.values()),
        'dataset': ['Training'] * len(train_counts)
    })
    
    test_df = pd.DataFrame({
        'disease': [disease_mapping[i] for i in test_counts.keys()],
        'count': list(test_counts.values()),
        'dataset': ['Testing'] * len(test_counts)
    })
    
    # Combine dataframes
    distribution_df = pd.concat([train_df, test_df])
    
    # Plot distribution
    plt.figure(figsize=(15, 10))
    
    # Get top 15 diseases by frequency for better visualization
    top_diseases = train_df.nlargest(15, 'count')['disease'].tolist()
    plot_df = distribution_df[distribution_df['disease'].isin(top_diseases)]
    
    sns.barplot(x='disease', y='count', hue='dataset', data=plot_df)
    plt.title('Distribution of Top 15 Diseases in Training and Testing Sets')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('disease_distribution.png')
    
    # Return full distribution data
    return distribution_df


# Function to analyze feature importance
def analyze_feature_importance(model, X_train, feature_names):
    # Get feature importances
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Plot the top 20 features
    plt.figure(figsize=(12, 8))
    top_n = 20
    top_indices = indices[:top_n]
    plt.title('Top 20 Feature Importances')
    plt.bar(range(top_n), importances[top_indices], align='center')
    plt.xticks(range(top_n), [feature_names[i] for i in top_indices], rotation=90)
    plt.tight_layout()
    plt.savefig('feature_importance.png')
    
    # Return as DataFrame for further analysis
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    return importance_df


# Function to analyze model performance
def analyze_model_performance(model, X_train, y_train, X_test, y_test, disease_mapping):
    # Confusion matrix
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    
    # Plot confusion matrix
    plt.figure(figsize=(14, 12))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=[disease_mapping[i] for i in range(len(disease_mapping))],
               yticklabels=[disease_mapping[i] for i in range(len(disease_mapping))])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    
    # Cross-validation scores
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    
    # Learning curve
    train_sizes, train_scores, test_scores = learning_curve(
        model, X_train, y_train, cv=5, n_jobs=-1, 
        train_sizes=np.linspace(0.1, 1.0, 10))
    
    # Plot learning curve
    plt.figure(figsize=(10, 6))
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)
    
    plt.plot(train_sizes, train_mean, 'o-', color='r', label='Training score')
    plt.plot(train_sizes, test_mean, 'o-', color='g', label='Cross-validation score')
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='r')
    plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1, color='g')
    plt.xlabel('Training examples')
    plt.ylabel('Score')
    plt.title('Learning Curve')
    plt.legend(loc='best')
    plt.grid(True)
    plt.savefig('learning_curve.png')
    
    # Return metrics
    return {
        'cv_scores': cv_scores,
        'cv_mean': np.mean(cv_scores),
        'cv_std': np.std(cv_scores)
    }


# Function to analyze symptoms patterns
def analyze_symptom_patterns(X_train, y_train, disease_mapping):
    # Convert to DataFrame for easier analysis
    train_df = X_train.copy()
    train_df['prognosis'] = y_train
    
    # Get symptom counts by disease
    symptom_by_disease = {}
    for disease_code in range(len(disease_mapping)):
        disease_data = train_df[train_df['prognosis'] == disease_code].drop('prognosis', axis=1)
        symptom_counts = disease_data.sum().sort_values(ascending=False)
        symptom_by_disease[disease_mapping[disease_code]] = symptom_counts
    
    # Plot top symptoms for the top 5 most common diseases
    disease_counts = train_df['prognosis'].value_counts().head(5)
    top_diseases = [disease_mapping[code] for code in disease_counts.index]
    
    fig, axes = plt.subplots(nrows=len(top_diseases), figsize=(12, 4*len(top_diseases)))
    
    for i, disease in enumerate(top_diseases):
        symptoms = symptom_by_disease[disease]
        top_symptoms = symptoms[symptoms > 0].head(10)
        
        if len(top_diseases) > 1:
            ax = axes[i]
        else:
            ax = axes
            
        sns.barplot(x=top_symptoms.values, y=top_symptoms.index, ax=ax)
        ax.set_title(f'Top 10 Symptoms for {disease}')
        ax.set_xlabel('Count')
    
    plt.tight_layout()
    plt.savefig('symptom_patterns.png')
    
    # Return the mapping for further analysis
    return symptom_by_disease


# Function to analyze symptom co-occurrence
def analyze_symptom_cooccurrence(X_train):
    # Select top symptoms for better visualization
    top_symptoms = X_train.sum().sort_values(ascending=False).head(15).index.tolist()
    X_subset = X_train[top_symptoms]
    
    # Compute correlation matrix
    corr_matrix = X_subset.corr()
    
    # Plot correlation heatmap
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, cmap='RdBu_r', vmin=-1, vmax=1, 
                annot=True, fmt='.2f', square=True, linewidths=.5)
    plt.title('Symptom Co-occurrence Correlation')
    plt.tight_layout()
    plt.savefig('symptom_cooccurrence.png')
    
    return corr_matrix


# Function to generate a comprehensive HTML report
def generate_html_report(results):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Disease Prediction Model Evaluation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin-bottom: 30px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #3498db; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .metric {{ font-weight: bold; margin-right: 10px; }}
            .value {{ color: #2980b9; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Disease Prediction Model Evaluation Report</h1>
        
        <div class="section">
            <h2>Model Performance Summary</h2>
            <p><span class="metric">Accuracy:</span> <span class="value">{results['accuracy']:.4f}</span></p>
            <p><span class="metric">Cross-Validation Mean Accuracy:</span> <span class="value">{results['cv_results']['cv_mean']:.4f} ± {results['cv_results']['cv_std']:.4f}</span></p>
            
            <h3>Performance Visualizations</h3>
            <div>
                <h4>Confusion Matrix</h4>
                <img src="confusion_matrix.png" alt="Confusion Matrix">
            </div>
            <div>
                <h4>Learning Curve</h4>
                <img src="learning_curve.png" alt="Learning Curve">
            </div>
        </div>
        
        <div class="section">
            <h2>Feature Importance Analysis</h2>
            <p>Top 10 most important symptoms for disease prediction:</p>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Symptom</th>
                    <th>Importance Score</th>
                </tr>
    """
    
    # Add top 10 features to the table
    for i, (feature, importance) in enumerate(results['feature_importance'].head(10).values):
        html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{feature}</td>
                    <td>{importance:.4f}</td>
                </tr>
        """
        
    html += """
            </table>
            <div>
                <h4>Feature Importance Visualization</h4>
                <img src="feature_importance.png" alt="Feature Importance">
            </div>
        </div>
        
        <div class="section">
            <h2>Disease Distribution Analysis</h2>
            <div>
                <img src="disease_distribution.png" alt="Disease Distribution">
            </div>
            <p>The chart above shows the distribution of diseases in the training and testing datasets.</p>
        </div>
        
        <div class="section">
            <h2>Symptom Analysis</h2>
            <div>
                <h4>Symptom Co-occurrence</h4>
                <img src="symptom_cooccurrence.png" alt="Symptom Co-occurrence">
                <p>This heatmap shows how frequently certain symptoms occur together, which can help identify symptom clusters.</p>
            </div>
            <div>
                <h4>Disease-Specific Symptom Patterns</h4>
                <img src="symptom_patterns.png" alt="Symptom Patterns">
                <p>These charts show the most common symptoms for the top 5 diseases in the dataset.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write to file
    with open('model_evaluation_report.html', 'w') as f:
        f.write(html)
    
    print("HTML report generated: model_evaluation_report.html")


# Main execution block
if __name__ == "__main__":
    import os
    
    # Create directory for visualizations if it doesn't exist
    os.makedirs('visualizations', exist_ok=True)
    
    # Load and clean data
    print("Loading and cleaning data...")
    X_train, y_train, X_test, y_test, label_encoder, disease_mapping = load_and_clean_data()
    
    # Train the model or load if already exists
    if os.path.exists('svc.pkl'):
        print("Loading existing model...")
        with open('svc.pkl', 'rb') as f:
            model = pickle.load(f)
    else:
        print("Training new model...")
        model = train_and_save_model(X_train, y_train, X_train.columns.tolist())
    
    # Evaluate the model
    print("Evaluating model performance...")
    accuracy, report, y_pred = evaluate_model(model, X_test, y_test)
    print("Model Accuracy:", accuracy)
    print("Classification Report:\n", report)
    
    # Analyze class distribution
    print("Analyzing disease distribution...")
    distribution_df = analyze_class_distribution(y_train, y_test, disease_mapping)
    
    # Analyze feature importance
    print("Analyzing feature importance...")
    importance_df = analyze_feature_importance(model, X_train, X_train.columns.tolist())
    
    # Analyze model performance
    print("Analyzing detailed model performance...")
    cv_results = analyze_model_performance(model, X_train, y_train, X_test, y_test, disease_mapping)
    
    # Analyze symptom patterns
    print("Analyzing symptom patterns...")
    symptom_by_disease = analyze_symptom_patterns(X_train, y_train, disease_mapping)
    
    # Analyze symptom co-occurrence
    print("Analyzing symptom co-occurrence...")
    corr_matrix = analyze_symptom_cooccurrence(X_train)
    
    # Compile results
    results = {
        'accuracy': accuracy,
        'report': report,
        'distribution': distribution_df,
        'feature_importance': importance_df,
        'cv_results': cv_results,
        'symptom_by_disease': symptom_by_disease,
        'corr_matrix': corr_matrix
    }
    
    # Generate HTML report
    print("Generating comprehensive HTML report...")
    generate_html_report(results)
    
    # Save detailed results to CSV files
    importance_df.to_csv('feature_importance.csv', index=False)
    distribution_df.to_csv('disease_distribution.csv', index=False)
    
    print("\nEvaluation analysis completed successfully!")
    print("Generated files:")
    print("- model_evaluation_report.html (comprehensive visual report)")
    print("- disease_distribution.png")
    print("- feature_importance.png")
    print("- confusion_matrix.png")
    print("- learning_curve.png")
    print("- symptom_patterns.png")
    print("- symptom_cooccurrence.png")
    print("- feature_importance.csv")
    print("- disease_distribution.csv")