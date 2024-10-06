import requests
from tqdm import tqdm


def download_file(
        url: str,
        output_path: str,
        session: requests.Session = None,
) -> None:
    # Streaming, so we can iterate over the response.
    if session is None:
        response = requests.get(url, stream=True)
    else:
        response = session.get(url, stream=True)

    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024

    with tqdm(total=total_size, unit="B", unit_scale=True, leave=False) as progress_bar:
        with open(output_path, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

    if total_size != 0 and progress_bar.n != total_size:
        raise RuntimeError("Could not download file")
