from datetime import datetime, timedelta
import os
import sys
import pandas as pd
import pytz

# Ensure project root is on sys.path so we can import the app module.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from streamlit_app import filter_df_to_current_month


def test_filter_df_to_current_month():
    tz = pytz.timezone('America/Puerto_Rico')
    now = datetime.now(tz)

    # Fecha en el mes actual
    current = tz.localize(datetime(now.year, now.month, 5, 12, 0))

    # Fecha en el mes anterior
    first_of_month = tz.localize(datetime(now.year, now.month, 1, 0, 0))
    prev = first_of_month - timedelta(days=1)

    df = pd.DataFrame({'fecha': [current, prev]})

    filtered = filter_df_to_current_month(df)

    assert len(filtered) == 1
    assert filtered['fecha'].dt.month.iloc[0] == now.month


if __name__ == '__main__':
    test_filter_df_to_current_month()
    print('test_filter_df_to_current_month passed')
