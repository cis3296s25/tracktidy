import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
import pytest
from unittest.mock import patch, MagicMock
from src.tracktidy.batch.processor import batch_process, get_files_for_batch
from src.tracktidy.core.cover_art import get_spotify_credentials, search_track, download_cover_art
from src.tracktidy.services.spotify import validate_spotify_credentials

# Mocking the Console to avoid actual prints during tests
@pytest.fixture
def mock_console():
    with patch('rich.console.Console.print') as mock_print:
        yield mock_print

# Mocking the Prompt.ask for user input
@pytest.fixture
def mock_prompt():
    with patch('rich.prompt.Prompt.ask') as mock_ask:
        yield mock_ask

# Mocking Confirm.ask for yes/no questions
@pytest.fixture
def mock_confirm():
    with patch('rich.prompt.Confirm.ask') as mock_confirm:
        yield mock_confirm

# ---- TESTING batch_process ----
@pytest.mark.asyncio
async def test_batch_process(mock_prompt, mock_console):
    # Simulate user input for choosing batch option 1 (metadata editing)
    mock_prompt.return_value = "1"

    # Call the batch process function
    await batch_process()

    # Assert that the batch_metadata function was called (since we selected option 1)
    mock_console.assert_any_call("[#89b4fa]1.[/#89b4fa][bold] Batch Metadata Editing[/bold]")

# ---- TESTING get_files_for_batch ----
@pytest.mark.asyncio
async def test_get_files_for_batch_valid_directory(mock_prompt, mock_console):
    # Simulating a valid directory
    mock_prompt.return_value = "/mock/directory"
    
    with patch('os.path.isdir', return_value=True):
        with patch('glob.glob', return_value=["/mock/directory/file1.mp3", "/mock/directory/file2.mp3"]):
            files = await get_files_for_batch(file_type="audio")
            assert len(files) == 2  # Two files found
            assert "/mock/directory/file1.mp3" in files
            assert "/mock/directory/file2.mp3" in files

@pytest.mark.asyncio
async def test_get_files_for_batch_invalid_directory(mock_prompt, mock_console):
    print("Starting invalid dir test")
    mock_prompt.return_value = "/invalid/directory"  # Mock invalid directory input
    mock_confirm.return_value = False  # Mock 'No' for retrying
    
    with patch('os.path.isdir', return_value=False):  # Simulating invalid directory
        files = await get_files_for_batch(file_type="audio")
        print("Finished invalid dir test")  # This should print if test continues
        assert files == []  # No files found due to invalid directory

# ---- TESTING cover_art.py ----
@pytest.mark.parametrize("client_id, client_secret, expected_result", [
    ("valid_id", "valid_secret", True),
    ("", "", False),
    ("invalid_id", "invalid_secret", False)
])
def test_validate_spotify_credentials(client_id, client_secret, expected_result, mock_console):
    result = validate_spotify_credentials(client_id, client_secret)
    assert result == expected_result

@patch('requests.get')
def test_download_cover_art(mock_get):
    # Simulate a successful download
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"image data"
    result = download_cover_art("http://mockurl.com")
    assert result == b"image data"

    # Simulate a failed download
    mock_get.return_value.status_code = 404
    result = download_cover_art("http://invalidurl.com")
    assert result is None

# ---- TESTING get_spotify_credentials ----
@patch('builtins.open', new_callable=MagicMock)
def test_get_spotify_credentials(mock_open, mock_console):
    # Simulating a valid credentials file
    mock_open.return_value.read.return_value = '{"client_id": "valid_id", "client_secret": "valid_secret"}'
    
    result = get_spotify_credentials()
    assert result == ("valid_id", "valid_secret")

    # Simulating an invalid credentials file
    mock_open.return_value.read.return_value = '{"client_id": "invalid_id", "client_secret": "invalid_secret"}'
    result = get_spotify_credentials()
    assert result == ("", "")
