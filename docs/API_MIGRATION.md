# 🔄 Kalshi API Migration Notice

## Important Update

Kalshi has migrated their API from the old endpoint to a new one. This tool has been updated to work with the new API.

## What Changed

- **Old API**: `https://trading-api.kalshi.com/trade-api/v2`
- **New API**: `https://api.elections.kalshi.com`

## What You Need to Do

### 1. Update Your Configuration

If you have an existing `.env` file, update the API URL:

```env
# Old (deprecated)
KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2

# New (current)
KALSHI_API_URL=https://api.elections.kalshi.com
```

### 2. Verify Your API Key

Make sure your Kalshi API key is still valid and has the necessary permissions for the new endpoint.

### 3. Test the Connection

Run the test script to verify everything is working:

```bash
python test_setup.py
```

## API Documentation

The new API documentation is available at:
- **Documentation**: [https://docs.kalshi.com](https://docs.kalshi.com)
- **Changelog**: [https://docs.kalshi.com/changelog](https://docs.kalshi.com/changelog)

## Support

If you encounter any issues with the new API:

1. Check the [Kalshi API documentation](https://docs.kalshi.com)
2. Join the [Kalshi Discord](https://help.kalshi.com/account-and-login/kalshi-api) #dev channel
3. Verify your API key permissions
4. Check the tool's error messages for specific guidance

## Version Compatibility

This tool has been updated to work with the new API endpoint. If you're using an older version, please update to the latest version to ensure compatibility.

## What's New

The new API endpoint should provide:
- Better performance
- More reliable service
- Updated documentation
- Enhanced features

## Troubleshooting

### Common Issues

**"API request failed"**
- Verify the new API URL is correct
- Check your API key is valid
- Ensure you have internet connectivity

**"Authentication failed"**
- Verify your API key is correct
- Check if your API key has expired
- Ensure you're using the correct authentication method

**"Endpoint not found"**
- Make sure you're using the latest version of the tool
- Check that the API endpoint is correct
- Verify the API documentation for any endpoint changes

If you continue to have issues, please check the [troubleshooting section](README.md#troubleshooting) in the main README.



