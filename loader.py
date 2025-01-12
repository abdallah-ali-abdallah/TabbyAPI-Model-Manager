import streamlit as st
import requests
import os
import subprocess

# Constants
DEFAULT_MODEL = "Press Fetch to list all available models"
DEFAULT_MODELS_PATH = "models"
DEFAULT_API_KEY = "tabby"
LOAD_ENDPOINT = "/v1/model/load"
UNLOAD_ENDPOINT = "/v1/model/unload"
MODELS_ENDPOINT = "/v1/models"

# Session state to store the list of models
if 'models' not in st.session_state:
    st.session_state.models = []
if 'draft_models' not in st.session_state:
    st.session_state.draft_models = []


# Function to fetch the list of models from the API
def fetch_models(api_key, tabby_host):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(f"{tabby_host}{MODELS_ENDPOINT}", headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        models_response = response.json()
        
        # Clear previous models
        st.session_state.models = []
        st.session_state.draft_models = []
        
        # Extract model names from response
        if isinstance(models_response, dict) and "data" in models_response:
            models_data = models_response["data"]
            if isinstance(models_data, list):
                for model in models_data:
                    if isinstance(model, dict) and "id" in model:
                        st.session_state.models.append(model["id"])
                        st.session_state.draft_models.append(model["id"])
                
                if st.session_state.models:
                    st.success(f"Successfully fetched {len(st.session_state.models)} models")
                else:
                    st.warning("No models found in the response")
            else:
                st.error("Invalid data format in API response. Expected a list of models.")
        else:
            st.error("Invalid response format from the API. Expected a dictionary with 'data' key.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching models: {str(e)}")

# Function to unload model
def _unload_model(api_key, tabby_host):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.post(f"{tabby_host}{UNLOAD_ENDPOINT}", headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        st.success(f"Model Unloaded: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

# Function to load single model
def _load_single_model(api_key, tabby_host, model_name, cache_mode, num_experts_per_token,
                      max_seq_length, gpu_split, autosplit_reserve, tensor_parallel, prompt_template, use_prompt_template):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "name": model_name
    }
    # Add prompt template only if checkbox is enabled
    if use_prompt_template:
        data["prompt_template"] = prompt_template
    if num_experts_per_token:
        data["num_experts_per_token"] = num_experts_per_token
    if cache_mode:
        data["cache_mode"] = cache_mode
    if max_seq_length:
        data["max_seq_length"] = max_seq_length
    if gpu_split:
        gpu_split_array = gpu_split.split()
        data["gpu_split"] = gpu_split_array
    if not gpu_split:
        data["gpu_split_auto"] = True
    data["tensor_parallel"] = tensor_parallel
    if autosplit_reserve and not gpu_split:
        autosplit_reserve_array = autosplit_reserve.split()
        data["autosplit_reserve"] = autosplit_reserve_array
        
    try:
        st.write("Sending request with JSON data:")
        st.json(data)
        response = requests.post(f"{tabby_host}{LOAD_ENDPOINT}", headers=headers, json=data)
        response.raise_for_status()
        st.success(f"Model Loaded: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

# Function to load both main and draft models
def _load_both_models(api_key, tabby_host, model_name, draft_model_name, cache_mode, draft_cache_mode, 
                     num_experts_per_token, max_seq_length, gpu_split, autosplit_reserve, tensor_parallel, prompt_template, use_prompt_template):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "name": model_name,
        "draft": {
            "draft_model_name": draft_model_name,
            "draft_cache_mode": draft_cache_mode
        }
    }
    # Add prompt template only if checkbox is enabled
    if use_prompt_template:
        data["prompt_template"] = prompt_template
    if num_experts_per_token:
        data["num_experts_per_token"] = num_experts_per_token
    if cache_mode:
        data["cache_mode"] = cache_mode
    if max_seq_length:
        data["max_seq_length"] = max_seq_length
    if gpu_split:
        gpu_split_array = gpu_split.split()
        data["gpu_split"] = gpu_split_array
    if not gpu_split:
        data["gpu_split_auto"] = True
    data["tensor_parallel"] = tensor_parallel
    if autosplit_reserve and not gpu_split:
        autosplit_reserve_array = autosplit_reserve.split()
        data["autosplit_reserve"] = autosplit_reserve_array
        
    try:
        st.write("Sending request with JSON data:")
        st.json(data)
        response = requests.post(f"{tabby_host}{LOAD_ENDPOINT}", headers=headers, json=data)
        response.raise_for_status()
        st.success(f"Models Loaded: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

# Function to clean and format the API URL
def format_api_url(address, port):
    if not address.startswith("http://") and not address.startswith("https://"):
        address = f"http://{address}"
    return f"{address}:{port}".rstrip("/")

# Streamlit App
st.set_page_config(layout="wide")
st.title("TabbyAPI Model Manager")

# Create three columns with adjusted spacing
col1, col2, col3 = st.columns([1, 1.2, 1])

# Left Column - Server Configuration
with col1:
    st.header("Server Configuration")
    server_address = st.text_input("Server Address", value="localhost")
    server_port = st.text_input("Server Port", value="5001")
    api_key = st.text_input("API Key", value=DEFAULT_API_KEY, type="password")
    
    # Add prompt template controls
    use_prompt_template = st.checkbox("Use Custom Prompt Template", value=False)
    prompt_template = st.text_input("Prompt Template", value="chatml_with_headers.jinja", disabled=not use_prompt_template)
    st.markdown("[How to add tool calling support with chat templates](https://github.com/theroyallab/tabbyAPI/wiki/10.-Tool-Calling)")
    

# Middle Column - Model Configuration
with col2:
    st.header("Model Configuration")
    # Store model names in session state to persist selections
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = DEFAULT_MODEL
    if 'selected_draft_model' not in st.session_state:
        st.session_state.selected_draft_model = DEFAULT_MODEL

    if st.session_state.models:
        st.session_state.selected_model = st.selectbox(
            "Model Name", 
            options=st.session_state.models,
            index=st.session_state.models.index(st.session_state.selected_model) 
            if st.session_state.selected_model in st.session_state.models 
            else 0
        )
    else:
        st.session_state.selected_model = st.text_input("Model Name", value=DEFAULT_MODEL)

    if st.session_state.draft_models:
        st.session_state.selected_draft_model = st.selectbox(
            "Draft Model Name", 
            options=st.session_state.draft_models,
            index=st.session_state.draft_models.index(st.session_state.selected_draft_model)
            if st.session_state.selected_draft_model in st.session_state.draft_models
            else 0
        )
    else:
        st.session_state.selected_draft_model = st.text_input("Draft Model Name", value=DEFAULT_MODEL)

    models_path = st.text_input("Models Path (Internal server folder)", value=DEFAULT_MODELS_PATH)

    # Cache Mode Dropdowns
    cache_mode = st.selectbox("Cache Mode for Inference Model", options=["FP16", "Q8", "Q6", "Q4"], index=0)
    draft_cache_mode = st.selectbox("Cache Mode for Draft Model", options=["FP16", "Q8", "Q6", "Q4"], index=0)

    num_experts_per_token = st.number_input("Experts per Token", value=0)
    max_seq_length = st.number_input("Max Sequence Length", value=0, min_value=0)
    gpu_split = st.text_input("GPU Split (e.g., 14 15 15)", value="")
    autosplit_reserve = st.text_input("Autosplit Reserve (e.g., 96 96 96)", value="")

# Right Column - Actions and Info
with col3:
    st.header("Actions")
    no_unload = st.checkbox("Load Model(s) without unloading previous models")
    tensor_parallel = st.checkbox("Tensor Parallel", value=True)
    
    # Fetch Models Button
    fetch_models_button = st.button("Fetch Models")
    if fetch_models_button:
        if api_key:
            tabby_host = format_api_url(server_address, server_port)
            fetch_models(api_key, tabby_host)
            # Force Streamlit to re-run and update the UI
            st.rerun()
        else:
            st.error("Please provide an API Key to fetch models.")
            
    unload_model = st.button("Unload Model")
    load_single_model = st.button("Load Main Model Only")
    load_model_draft = st.button("Load Model + Draft")

    # API URL
    tabby_host = format_api_url(server_address, server_port)

    # Action Handlers
    if unload_model and not no_unload:
        _unload_model(api_key, tabby_host)

    if load_single_model:
        _load_single_model(api_key, tabby_host, st.session_state.selected_model, cache_mode, num_experts_per_token,
                          max_seq_length, gpu_split, autosplit_reserve, tensor_parallel, prompt_template, use_prompt_template)

    if load_model_draft:
        if not st.session_state.selected_draft_model or st.session_state.selected_draft_model == DEFAULT_MODEL:
            st.error("Please select a draft model from the dropdown")
        else:
            _load_both_models(api_key, tabby_host, st.session_state.selected_model, st.session_state.selected_draft_model, cache_mode, draft_cache_mode,
                            num_experts_per_token, max_seq_length, gpu_split, autosplit_reserve, tensor_parallel, prompt_template, use_prompt_template)
