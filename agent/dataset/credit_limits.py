import pandas as pd
import numpy as np

# --- Định nghĩa 5 bộ hệ số hồi quy dựa trên tài liệu credit_limits.txt ---
# Công thức:
# CL = β1*Rev_90d + β2*Growth_sc + β3*Txn_freq_sc - β4*CV_sc - β5*Spike_sc - β6*Default_prob - β7*CIC_sc
# Các cột tương ứng:
# 'Revenue_mean_90d', 'Growth_score', 'Txn_freq_score', 'CV_score', 'Spike_score', 'default_probability', 'CIC_SCORE'

COEFFICIENT_SETS = {
    'Conservative': {
        'coeffs': (1.5, 0.3, 0.2, 0.6, 0.5, 1.2, 0.4),
        'NOTE': 'Ưu tiên an toàn, phạt mạnh các yếu tố rủi ro và biến động.'
    },
    'Balanced': {
        'coeffs': (2.5, 0.6, 0.4, 0.5, 0.4, 1.0, 0.3),
        'NOTE': 'Cân bằng giữa các yếu tố tăng trưởng và rủi ro.'
    },
    'Growth-driven': {
        'coeffs': (3.5, 1.2, 0.8, 0.3, 0.2, 0.8, 0.2),
        'NOTE': 'Ưu tiên các doanh nghiệp có tiềm năng tăng trưởng, chấp nhận rủi ro cao hơn.'
    },
    'Stability-focused': {
        'coeffs': (2.2, 0.4, 0.3, 0.9, 0.8, 1.0, 0.3),
        'NOTE': 'Ưu tiên các doanh nghiệp có dòng tiền ổn định, phạt mạnh yếu tố biến động.'
    },
    'Risk-based': {
        'coeffs': (2.8, 0.5, 0.4, 0.5, 0.4, 1.5, 0.5),
        'NOTE': 'Định hướng theo rủi ro, xác suất vỡ nợ (default_probability) có tác động chi phối.'
    }
}

# Ánh xạ tên biến trong công thức với tên cột trong DataFrame
VAR_NAMES = [
    'Revenue_mean_90d', 'Growth_score', 'Txn_freq_score', 
    'CV_score', 'Spike_score', 'default_probability', 'CIC_SCORE'
]

def calculate_credit_limit(customer_data: pd.Series, coefficient_set_name: str) -> int:
    """
    Tính toán hạn mức tín dụng đề xuất cho khách hàng dựa trên công thức và bộ hệ số đã chọn.

    Args:
        customer_data (pd.Series): Dữ liệu của một khách hàng.
        coefficient_set_name (str): Tên của bộ hệ số hồi quy muốn sử dụng.

    Returns:
        int: Hạn mức tín dụng đề xuất, đã được làm tròn xuống hàng trăm triệu.
    """
    if coefficient_set_name not in COEFFICIENT_SETS:
        raise ValueError(f"Bộ hệ số '{coefficient_set_name}' không tồn tại. Các lựa chọn: {list(COEFFICIENT_SETS.keys())}")

    # --- LOGIC MỚI: Thêm hạn mức nền theo nhóm CIC ---
    cic_range = customer_data.get('label_cic_range', 'Poor').upper() # Lấy nhóm CIC, mặc định là 'POOR'
    base_limit_mil = 50  # Mức nền tối thiểu là 50 triệu
    if cic_range == 'FAIR':
        base_limit_mil = 100
    elif cic_range == 'GOOD':
        base_limit_mil = 150
    elif cic_range == 'EXCELLENT':
        base_limit_mil = 200
    # 'VERY POOR' và 'POOR' giữ nguyên mức 50 triệu

    # Lấy bộ hệ số tương ứng
    b = COEFFICIENT_SETS[coefficient_set_name]['coeffs']
    
    # Lấy dữ liệu từ các cột, nếu thiếu thì dùng giá trị 0 hoặc giá trị trung bình hợp lý
    # Revenue_mean_90d được chia cho 1,000,000 để đưa về đơn vị triệu VND cho cân xứng với các score
    rev_90d = customer_data.get('Revenue_mean_90d', 0) / 1_000_000
    growth_sc = customer_data.get('Growth_score', 0)
    txn_freq_sc = customer_data.get('Txn_freq_score', 0)
    cv_sc = customer_data.get('CV_score', 0)
    spike_sc = customer_data.get('Spike_score', 0)
    default_prob = customer_data.get('default_probability', 0.5) # Giả định mức rủi ro trung bình nếu thiếu
    cic_sc = customer_data.get('CIC_SCORE', 500) # Giả định điểm CIC trung bình nếu thiếu

    # Áp dụng công thức hồi quy để tính phần hạn mức BỔ SUNG
    additional_limit_mil = (
        b[0] * rev_90d +
        b[1] * growth_sc +
        b[2] * txn_freq_sc -
        b[3] * cv_sc -
        b[4] * spike_sc -
        b[5] * default_prob -
        b[6] * cic_sc
    )
    
    # Hạn mức cuối cùng = Hạn mức nền + Hạn mức bổ sung
    # Đảm bảo phần bổ sung không kéo tổng hạn mức xuống dưới 0
    total_limit_mil = base_limit_mil + additional_limit_mil
    total_limit_mil = max(0, total_limit_mil)

    # Chuyển về đơn vị VND
    limit_suggestion_vnd = total_limit_mil * 1_000_000

    # Làm tròn xuống đến hàng trăm triệu gần nhất
    rounded_limit = int(np.floor(limit_suggestion_vnd / 100_000_000) * 100_000_000)

    return rounded_limit

def get_coefficient_note(coefficient_set_name: str) -> str:
    """Lấy ghi chú về bộ hệ số được chọn."""
    if coefficient_set_name not in COEFFICIENT_SETS:
        return "Bộ hệ số không xác định."
    return COEFFICIENT_SETS[coefficient_set_name].get('NOTE', 'Không có ghi chú.')

# Đổi tên REGRESSION_COEFFICIENTS để phù hợp với notebook
REGRESSION_COEFFICIENTS = COEFFICIENT_SETS

if __name__ == '__main__':
    # Ví dụ cách sử dụng với dữ liệu giả định theo đúng format
    mock_customer = pd.Series({
        'Revenue_mean_90d': 250_000_000,
        'Growth_score': 80,
        'Txn_freq_score': 70,
        'CV_score': 30,
        'Spike_score': 20,
        'default_probability': 0.1,
        'CIC_SCORE': 650
    })

    print("Ví dụ tính toán hạn mức tín dụng với 5 bộ hệ số mới:")
    for model_name in COEFFICIENT_SETS.keys():
        note = get_coefficient_note(model_name)
        limit = calculate_credit_limit(mock_customer, coefficient_set_name=model_name)
        print(f"\n--- Mô hình: {model_name} ---")
        print(f"Ghi chú: {note}")
        print(f"Hạn mức đề xuất: {limit:,.0f} VND")

