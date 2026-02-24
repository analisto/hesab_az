import kagglehub
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for better-looking plots
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)

BASE_DIR = Path(__file__).resolve().parent.parent
CHARTS_DIR = BASE_DIR / 'charts'
MODEL_DIR = BASE_DIR / 'model'

# Create output folders if they don't exist
CHARTS_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Download latest version
path = kagglehub.dataset_download("muhammadshahidazeem/customer-churn-dataset")

print("Path to dataset files:", path)

# Find the CSV file in the downloaded path
import os
csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
print(f"Found CSV files: {csv_files}")

# Load the dataset
df = pd.read_csv(os.path.join(path, csv_files[0]))
print(f"\nDataset shape: {df.shape}")
df.head()

# Basic information
print("Dataset Info:")
print(df.info())
print("\nBasic Statistics:")
df.describe()

# Check for missing values
print("Missing Values:")
missing = df.isnull().sum()
missing[missing > 0]

# Check churn distribution
if 'Churn' in df.columns:
    churn_col = 'Churn'
elif 'churn' in df.columns:
    churn_col = 'churn'
else:
    # Find column that might be churn
    churn_candidates = [col for col in df.columns if 'churn' in col.lower()]
    churn_col = churn_candidates[0] if churn_candidates else df.columns[-1]

print(f"Churn Distribution:")
print(df[churn_col].value_counts())
print(f"\nChurn Rate: {df[churn_col].value_counts(normalize=True).iloc[1]:.2%}")

# Churn distribution pie chart
plt.figure(figsize=(8, 6))
df[churn_col].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=['#66b3ff', '#ff6666'])
plt.title('Churn Distribution', fontsize=14, fontweight='bold')
plt.ylabel('')
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'churn_distribution.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'churn_distribution.png'}")

# Correlation heatmap for numerical features
numerical_cols = df.select_dtypes(include=[np.number]).columns
plt.figure(figsize=(12, 10))
correlation = df[numerical_cols].corr()
sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Feature Correlation Heatmap', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'correlation_heatmap.png'}")

# Distribution of numerical features
numerical_features = df[numerical_cols].columns.tolist()
if churn_col in numerical_features:
    numerical_features.remove(churn_col)

n_features = min(6, len(numerical_features))  # Show top 6 features
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.ravel()

for idx, col in enumerate(numerical_features[:n_features]):
    axes[idx].hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
    axes[idx].set_title(f'Distribution of {col}', fontweight='bold')
    axes[idx].set_xlabel(col)
    axes[idx].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig(CHARTS_DIR / 'feature_distributions.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'feature_distributions.png'}")

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Create a copy for preprocessing
df_processed = df.copy()

# Handle missing values
for col in df_processed.columns:
    if df_processed[col].isnull().sum() > 0:
        if df_processed[col].dtype in ['float64', 'int64']:
            df_processed[col].fillna(df_processed[col].median(), inplace=True)
        else:
            df_processed[col].fillna(df_processed[col].mode()[0], inplace=True)

# Encode categorical variables
label_encoders = {}
categorical_cols = df_processed.select_dtypes(include=['object']).columns

for col in categorical_cols:
    if col != churn_col:
        le = LabelEncoder()
        df_processed[col] = le.fit_transform(df_processed[col].astype(str))
        label_encoders[col] = le

# Encode target variable
if df_processed[churn_col].dtype == 'object':
    le_target = LabelEncoder()
    df_processed[churn_col] = le_target.fit_transform(df_processed[churn_col])

print(f"Processed dataset shape: {df_processed.shape}")
df_processed.head()

# Split features and target
X = df_processed.drop(churn_col, axis=1)
y = df_processed[churn_col]

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training set size: {X_train.shape[0]}")
print(f"Test set size: {X_test.shape[0]}")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import confusion_matrix, classification_report, roc_curve

# Initialize models
models = {
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42)
}

# Train and evaluate models
results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)
    
    # Predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Metrics
    results[name] = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba),
        'model': model,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba
    }
    
    print(f"{name} - Accuracy: {results[name]['accuracy']:.4f}, "
          f"Precision: {results[name]['precision']:.4f}, "
          f"Recall: {results[name]['recall']:.4f}, "
          f"F1: {results[name]['f1']:.4f}, "
          f"ROC AUC: {results[name]['roc_auc']:.4f}")

# Compare model performance
metrics_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Accuracy': [results[m]['accuracy'] for m in results.keys()],
    'Precision': [results[m]['precision'] for m in results.keys()],
    'Recall': [results[m]['recall'] for m in results.keys()],
    'F1 Score': [results[m]['f1'] for m in results.keys()],
    'ROC AUC': [results[m]['roc_auc'] for m in results.keys()]
})

print("\nModel Performance Comparison:")
print(metrics_df.to_string(index=False))

# Plot comparison
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(results))
width = 0.15

metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999', '#c2c2f0']

for i, metric in enumerate(metrics):
    values = [results[m][metric] for m in results.keys()]
    ax.bar(x + i*width, values, width, label=metric.upper().replace('_', ' '), color=colors[i])

ax.set_xlabel('Models', fontweight='bold')
ax.set_ylabel('Score', fontweight='bold')
ax.set_title('Model Performance Comparison', fontweight='bold', fontsize=14)
ax.set_xticks(x + width * 2)
ax.set_xticklabels(results.keys())
ax.legend()
ax.set_ylim([0, 1.1])
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'model_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'model_comparison.png'}")

# Plot ROC curves for all models
plt.figure(figsize=(10, 8))

for name in results.keys():
    fpr, tpr, _ = roc_curve(y_test, results[name]['y_pred_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {results[name]['roc_auc']:.3f})", linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=2)
plt.xlabel('False Positive Rate', fontweight='bold')
plt.ylabel('True Positive Rate', fontweight='bold')
plt.title('ROC Curves Comparison', fontweight='bold', fontsize=14)
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'roc_curves.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'roc_curves.png'}")

# Find best model
best_model_name = max(results, key=lambda x: results[x]['f1'])
best_model = results[best_model_name]['model']

print(f"\nBest Model: {best_model_name}")
print(f"F1 Score: {results[best_model_name]['f1']:.4f}")

# Confusion matrix for best model
cm = confusion_matrix(y_test, results[best_model_name]['y_pred'])

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=True, 
            xticklabels=['No Churn', 'Churn'], 
            yticklabels=['No Churn', 'Churn'])
plt.title(f'Confusion Matrix - {best_model_name}', fontweight='bold', fontsize=14)
plt.ylabel('Actual', fontweight='bold')
plt.xlabel('Predicted', fontweight='bold')
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"Saved: {CHARTS_DIR / 'confusion_matrix.png'}")

# Classification report
print(f"\nClassification Report - {best_model_name}:")
print(classification_report(y_test, results[best_model_name]['y_pred'], 
                          target_names=['No Churn', 'Churn']))

# Feature importance for tree-based models
if best_model_name in ['Random Forest', 'Gradient Boosting']:
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 8))
    top_features = feature_importance.head(15)
    plt.barh(range(len(top_features)), top_features['importance'], color='#66b3ff')
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance', fontweight='bold')
    plt.ylabel('Features', fontweight='bold')
    plt.title(f'Top 15 Feature Importances - {best_model_name}', fontweight='bold', fontsize=14)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'feature_importance.png', dpi=300, bbox_inches='tight')
    plt.show()
    print(f"Saved: {CHARTS_DIR / 'feature_importance.png'}")
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

import pickle

# Save the best model
model_data = {
    'model': best_model,
    'scaler': scaler,
    'feature_names': X.columns.tolist(),
    'model_name': best_model_name
}

model_path = MODEL_DIR / 'best_churn_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model_data, f)

print(f"Best model ({best_model_name}) saved to: {model_path}")

print("="*60)
print("CHURN PREDICTION MODEL SUMMARY")
print("="*60)
print(f"\nDataset: Customer Churn Dataset")
print(f"Total Records: {len(df)}")
print(f"Features: {X.shape[1]}")
print(f"Training Set: {len(X_train)} samples")
print(f"Test Set: {len(X_test)} samples")
print(f"\nBest Model: {best_model_name}")
print(f"  - Accuracy:  {results[best_model_name]['accuracy']:.4f}")
print(f"  - Precision: {results[best_model_name]['precision']:.4f}")
print(f"  - Recall:    {results[best_model_name]['recall']:.4f}")
print(f"  - F1 Score:  {results[best_model_name]['f1']:.4f}")
print(f"  - ROC AUC:   {results[best_model_name]['roc_auc']:.4f}")
print(f"\nCharts saved in: {CHARTS_DIR}")
print(f"Model saved as: {model_path}")
print("="*60)
