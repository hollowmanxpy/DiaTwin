import streamlit as st
import json
import time
from diatwin_fhir_generator import DiaTwinFHIRGenerator

st.set_page_config(page_title="DiaTwin 数据生成舱", page_icon="🧬", layout="wide")

st.title("🧬 DiaTwin 数字孪生数据生成舱 (Data Generator)")
st.markdown("""
<div style="background-color: #F0F8FF; padding: 15px; border-radius: 10px; border-left: 5px solid #30A5A7; margin-bottom: 25px;">
    <b>欢迎使用 DiaTwin RWD 合成引擎！</b><br>
    只需输入患者的临床基线切片数据，平台将结合代谢动力学算法，自动为您扩增连续多天的动态生理特征序列，并将其打包成符合国际 <b>HL7 FHIR R4</b> 标准的 JSON 格式包。
</div>
""", unsafe_allow_html=True)

with st.form("patient_form"):
    st.subheader("👤 第一步：配置患者数字身份与基线 (Patient Baseline)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        p_id = str(st.text_input("病例 ID*", value="DIA-TWIN-889", help="必填项，用于标识唯一患者"))
    with col2:
        p_name = str(st.text_input("患者姓名 (可匿名)", value="李雷"))
    with col3:
        # 安全拆包 None，彻底消灭所有类型不匹配的警告
        age_input = st.number_input("年龄", min_value=1, max_value=120, value=65, step=1)
        p_age = int(age_input) if age_input is not None else 65
    with col4:
        p_gender = str(st.selectbox("生理性别", ["male", "female", "other"]))

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        bmi_input = st.number_input("BMI (体质指数)", min_value=10.0, max_value=50.0, value=28.5, step=0.1)
        p_bmi = float(bmi_input) if bmi_input is not None else 28.5
    with col6:
        fpg_input = st.number_input("初始空腹血糖 FPG (mmol/L)", min_value=3.0, max_value=20.0, value=7.2, step=0.1)
        p_fpg = float(fpg_input) if fpg_input is not None else 7.2
    with col7:
        hba1c_input = st.number_input("糖化血红蛋白 HbA1c (%)", min_value=4.0, max_value=15.0, value=7.5, step=0.1)
        p_hba1c = float(hba1c_input) if hba1c_input is not None else 7.5
    with col8:
        p_comp = st.multiselect(
            "既往并发症",
            ["无并发症", "糖尿病肾病期", "糖尿病视网膜病变", "周围神经病变", "冠心病"],
            default=["糖尿病肾病期", "周围神经病变"]
        )

    st.subheader("⚙️ 第二步：配置孪生动力学参数 (Simulation Dynamics)")
    col9, col10 = st.columns(2)
    with col9:
        comp_input = st.slider("患者临床依从性 (Compliance) —— 将影响动态血糖走向", min_value=0.0, max_value=1.0,
                               value=0.65, step=0.01)
        p_compliance = float(comp_input) if comp_input is not None else 0.65
    with col10:
        days_input = st.number_input("数据扩增天数 (Days to Simulate)", min_value=7, max_value=365, value=30, step=1)
        sim_days = int(days_input) if days_input is not None else 30

    submitted = st.form_submit_button("🚀 一键生成数字孪生体 (Generate Digital Twin)", type="primary")

if submitted:
    if not p_id.strip():
        st.error("⚠️ 病例 ID 不能为空，请填写后重试！")
    else:
        baseline = {
            "patient_id": p_id, "name": p_name, "age": p_age, "gender": p_gender,
            "bmi": p_bmi, "base_fpg": p_fpg, "base_hba1c": p_hba1c, "compliance": p_compliance,
            "complications": p_comp if "无并发症" not in p_comp else []
        }

        with st.spinner("正在启动时珍引擎，合成多模态连续时间序列数据..."):
            try:
                time.sleep(0.5)
                generator = DiaTwinFHIRGenerator(patient_baseline=baseline, simulate_days=sim_days)
                bundle_data = generator.run_generation()

                st.toast("合成完毕！", icon="🎉")
                st.success(f"✅ 孪生体生成成功！算法成功为您扩增出 {len(bundle_data['entry'])} 条 FHIR 临床资源记录。")

                json_str = json.dumps(bundle_data, ensure_ascii=False, indent=2)

                colA, colB = st.columns([1, 3])
                with colA:
                    st.download_button(
                        label="📥 下载 FHIR JSON 数据包",
                        data=json_str,
                        file_name=f"{p_id}_DigitalTwin_FHIR.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    st.info("此 JSON 文件完全符合 HL7 FHIR R4 国际标准，可直接用于临床系统打通或 AI 训练。")

                with colB:
                    with st.expander("👀 展开预览 FHIR Bundle 原始代码", expanded=True):
                        st.json(bundle_data)

            except Exception as e:
                st.error(f"❌ 生成过程中遇到问题：{str(e)}")