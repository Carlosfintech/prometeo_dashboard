import pytest, pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from app.ml_service import predict

@pytest.mark.asyncio
async def test_predict_returns_expected_columns():
    df_dummy = pd.DataFrame({'user_id': [1, 2]})
    with patch('app.ml_service.generate_features', return_value=df_dummy) as mock_gen:
        dummy_probs = np.array([[0.1, 0.9], [0.8, 0.2]])
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = dummy_probs
        with patch('app.ml_service.model', mock_model):
            result = await predict(df_dummy)
    mock_gen.assert_called_once()
    assert set(result.columns) == {'user_id','probability','is_target','created_at'}
    assert len(result) == 2