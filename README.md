# NFCe Data Collector

NFCe QRcode reader to simplify financial control

## Requirements

- [Python 3.11](https://www.python.org/downloads/release/python-311/)
- [Pip 23.2.1](https://pypi.org/project/pip/)
- [Iriun Webcam](https://iriun.com/)

## Installation guide (Iriun Webcam)

1. Download the Iriun Webcam app on your phone

2. Download the Iriun Webcam app on your computer

3. Connect your phone to the same network as your computer

4. Open the Iriun Webcam app on your phone

5. Open the Iriun Webcam app on your computer

## Running the script

1. Create a virtual environment:

    ```bash
    python3.11 -m venv .nfce
    ```

2. Activate the virtual environment:

    ```bash
    source .nfce/bin/activate
    ```

3. Install the requirements:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the script:

    ```bash
    python main.py
    ```

5. Scan the QR code of the NFCes you want to organize

6. The data will be saved in a CSV file named `nfc_data.csv` so you can import it to your financial control software or spreadsheet.
