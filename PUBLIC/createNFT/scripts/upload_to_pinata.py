
import os
from pathlib import Path
import requests
import json
from scripts.helpful_scripts import (PINATA_URL)


def uploadToPinata(nimal, luvability):
    print('\n----------------- uploading to pinata...')
    filename = nimal + '.png'
    print(f'    file name: {filename}')
    filepath = './img/' + filename
    print(f'    file path: {filepath}')
    headers = {
        "pinata_api_key": os.getenv("PINATA_API_KEY"),
        "pinata_secret_api_key": os.getenv("PINATA_API_SECRET"),
    }

    with Path(filepath).open("rb") as fp:
        image_binary = fp.read()
        metadata = {
            "name": nimal,
            "description": "An image showcasing the beauty of nature",
            "tags": ["nature", "landscape", "photography"],
            "customField": "Custom value",
            # Add more metadata fields as needed
        }
        response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            files={"file": (filename, image_binary)},
            data={"pinataMetadata": json.dumps(metadata)},
            headers=headers,
        )

        # Handle the image response
        if response.status_code == 200:
            print("\n     Image Upload successful!")
            ipfsHash = response.json()["IpfsHash"]
            print("     Image IPFS Hash:", ipfsHash)
            imgURL  = PINATA_URL.format(ipfsHash)
            print(f"    view image @ \n{imgURL}")
        else:
            print("\nImage Upload failed!")
            print("Response:", response.text)
            sys.exit(0)

        headers = {
            "pinata_api_key": os.getenv("PINATA_API_KEY"),
            "pinata_secret_api_key": os.getenv("PINATA_API_SECRET"),
            "Content-Type": "application/json",  # Set the content type header
        }
        
        
        # Now upload metadata separately
        print('\nCreating/ uploading metadata file...')
        metadata = {
            "name": nimal,
            "description": f"A {nimal}",
            "image": imgURL,
            "tags": ["nature", "animals", "photography"],
            "luvability": luvability,
            # Add more metadata fields as needed
        }
        metadata_response = requests.post(
            "https://api.pinata.cloud/pinning/pinJSONToIPFS",
            data=json.dumps(metadata),
            headers=headers,
        )

        # Handle the metadata response
        if metadata_response.status_code == 200:
            print("Metadata Upload successful!")
            metadata_ipfs_hash = metadata_response.json()["IpfsHash"]
            metadata_url = f"https://gateway.pinata.cloud/ipfs/{metadata_ipfs_hash}"
            print("Metadata IPFS Hash:", metadata_ipfs_hash)
            print("    view metadata @:\n", metadata_url)
            print(f"    also view @: \n{PINATA_URL.format(metadata_ipfs_hash)}")
        else:
            print("\nMetadata Upload failed!")
            print("Response:", metadata_response.text)


        return ipfsHash, imgURL, metadata_url
