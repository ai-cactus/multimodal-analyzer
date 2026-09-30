#!/bin/bash
# Test script for the Advanced Compliance Analysis System
# This script demonstrates the iterative refinement workflow

set -e

echo "🧪 Advanced Compliance Analysis System - Test Script"
echo "===================================================="
echo ""

# Configuration
API_BASE="http://localhost:8000/api"
TEST_FILE="${1:-sample_policy.docx}"

if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Error: Test file '$TEST_FILE' not found"
    echo "Usage: $0 <path_to_test_document>"
    exit 1
fi

echo "📄 Test Document: $TEST_FILE"
echo ""

# Step 1: Submit document for analysis
echo "Step 1: Submitting document for iterative analysis..."
RESPONSE=$(curl -s -X POST "$API_BASE/documents/analyze" \
  -F "file=@$TEST_FILE" \
  -F "compliance_body=CARF" \
  -F "enable_iterations=true")

DOCUMENT_ID=$(echo "$RESPONSE" | jq -r '.document_id')
ITERATIONS=$(echo "$RESPONSE" | jq -r '.max_iterations')

echo "✅ Document submitted successfully"
echo "   Document ID: $DOCUMENT_ID"
echo "   Max Iterations: $ITERATIONS"
echo ""

# Step 2: Monitor progress
echo "Step 2: Monitoring analysis progress..."
echo "   (This may take several minutes depending on document complexity)"
echo ""

COMPLETED=false
ITERATION_COUNT=0

while [ "$COMPLETED" = false ]; do
    sleep 10  # Wait 10 seconds between checks
    
    STATUS_RESPONSE=$(curl -s "$API_BASE/documents/$DOCUMENT_ID/status")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    CURRENT_STEP=$(echo "$STATUS_RESPONSE" | jq -r '.current_step')
    HIGH_CONF=$(echo "$STATUS_RESPONSE" | jq -r '.high_confidence_count')
    MEDIUM_CONF=$(echo "$STATUS_RESPONSE" | jq -r '.medium_confidence_count')
    
    echo "   Status: $STATUS | Step: $CURRENT_STEP | High-Conf: $HIGH_CONF | Medium-Conf: $MEDIUM_CONF"
    
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        COMPLETED=true
        
        # Extract iteration history if available
        CONVERGED=$(echo "$STATUS_RESPONSE" | jq -r '.converged // false')
        ITER_HISTORY=$(echo "$STATUS_RESPONSE" | jq -r '.iteration_history // []')
        
        if [ "$ITER_HISTORY" != "[]" ]; then
            ITERATION_COUNT=$(echo "$ITER_HISTORY" | jq 'length')
        fi
    fi
done

echo ""
echo "✅ Analysis complete!"
echo ""

# Step 3: Display results summary
echo "Step 3: Results Summary"
echo "======================="

RESULT=$(curl -s "$API_BASE/documents/$DOCUMENT_ID/result")

TOTAL_HIGH=$(echo "$RESULT" | jq -r '.findings_summary.high_confidence_count')
TOTAL_MEDIUM=$(echo "$RESULT" | jq -r '.findings_summary.medium_confidence_count')
TOTAL_ELEMENTS=$(echo "$RESULT" | jq -r '.findings_summary.total_elements_analyzed')

echo "   Total Iterations: $ITERATION_COUNT"
echo "   Converged: $CONVERGED"
echo "   High-Confidence Findings: $TOTAL_HIGH"
echo "   Medium-Confidence Findings: $TOTAL_MEDIUM"
echo "   Elements Analyzed: $TOTAL_ELEMENTS"
echo ""

# Step 4: Show iteration progression (if available)
if [ "$ITERATION_COUNT" -gt 0 ]; then
    echo "Step 4: Iteration Progression"
    echo "=============================="
    
    STATUS_FULL=$(curl -s "$API_BASE/documents/$DOCUMENT_ID/status")
    echo "$STATUS_FULL" | jq -r '.iteration_history[] | "   Iteration \(.iteration): \(.high_confidence_findings) high-conf, \(.medium_confidence_findings) medium-conf - Converged: \(.converged)"'
    echo ""
fi

# Step 5: Download outputs
echo "Step 5: Downloading Outputs"
echo "==========================="

OUTPUT_DIR="./test_outputs_${DOCUMENT_ID}"
mkdir -p "$OUTPUT_DIR"

# Download color-coded redraft
if [ "$TOTAL_HIGH" -gt 0 ] || [ "$TOTAL_MEDIUM" -gt 0 ]; then
    echo "   Downloading color-coded redraft..."
    curl -s "$API_BASE/documents/$DOCUMENT_ID/redraft?mode=color_coded" \
        -o "$OUTPUT_DIR/redraft_color_coded.docx"
    echo "   ✅ Saved: $OUTPUT_DIR/redraft_color_coded.docx"
    
    echo "   Downloading clean redraft..."
    curl -s "$API_BASE/documents/$DOCUMENT_ID/redraft?mode=clean" \
        -o "$OUTPUT_DIR/redraft_clean.docx"
    echo "   ✅ Saved: $OUTPUT_DIR/redraft_clean.docx"
fi

# Download compliance report
echo "   Downloading compliance report (PDF)..."
curl -s "$API_BASE/documents/$DOCUMENT_ID/report?format=pdf" \
    -o "$OUTPUT_DIR/compliance_report.pdf"
echo "   ✅ Saved: $OUTPUT_DIR/compliance_report.pdf"

# Save JSON results
echo "   Saving JSON results..."
echo "$RESULT" > "$OUTPUT_DIR/findings.json"
echo "   ✅ Saved: $OUTPUT_DIR/findings.json"

echo ""
echo "🎉 Test Complete!"
echo ""
echo "Summary:"
echo "--------"
if [ "$CONVERGED" = "true" ]; then
    echo "✅ SUCCESS: Document converged to compliance in $ITERATION_COUNT iteration(s)"
    echo "   The clean redraft is fully compliant and ready for use!"
else
    echo "⚠️  PARTIAL: Document did not fully converge after $ITERATION_COUNT iteration(s)"
    echo "   Final document has $TOTAL_HIGH high-confidence gap(s)"
    echo "   Manual review recommended"
fi
echo ""
echo "All outputs saved to: $OUTPUT_DIR"
echo ""
echo "Sample findings (first 3):"
echo "$RESULT" | jq -r '.high_confidence_findings[:3][] | "  - [\(.finding_id)] \(.description[:80])..."' || true
echo ""
