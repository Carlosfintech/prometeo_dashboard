import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.ml_service import predict

@pytest.mark.asyncio
async def test_predict_returns_expected_columns():
    # Dummy input DataFrame
    df = pd.DataFrame({'user_id': [1, 2]})

    # Mock run_pipeline and model.predict_proba
    with patch('app.ml_service.run_pipeline', return_value=df) as mock_pipeline:
        dummy_probs = [[0.1, 0.9], [0.8, 0.2]]
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = dummy_probs
        with patch('app.ml_service.model', mock_model):
            result = await predict(df)
            # Ensure run_pipeline was called
            mock_pipeline.assert_called_once_with(df)
            # Check columns
            cols = list(result.columns)
            assert set(cols) == {'user_id', 'probability', 'pred_bin', 'created_at'}
            # Check values shape
            assert len(result) == 2 