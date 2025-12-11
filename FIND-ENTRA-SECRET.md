# How to Find Your Entra ID Client Secret in Azure Portal

## Step-by-Step Instructions

### Method 1: Via App Registrations (Most Common)

1. **Navigate to Entra ID**
   - Go to [Azure Portal](https://portal.azure.com)
   - Search for "Entra ID" or "Azure Active Directory" in the top search bar
   - Click on the service

2. **Find Your App Registration**
   - In the left menu, click **"App registrations"**
   - Click **"All applications"** tab
   - Find and click **"EVA Suite"** (Client ID: `e6b439ec-8ff5-43e9-b54c-90c0db989792`)

3. **View Certificates & Secrets**
   - In the left menu of your app, click **"Certificates & secrets"**
   - Click the **"Client secrets"** tab
   - You should see your existing secret(s) listed

4. **Get the Secret Value**
   - ⚠️ **IMPORTANT**: If the secret was created before, you can only see its **Description** and **Expiration date**
   - You **CANNOT** view the secret value again after creation
   - If you need the value and didn't save it:
     - You must create a **new secret**
     - Click **"+ New client secret"**
     - Add a description (e.g., "EVA API Secret - Dec 2025")
     - Choose expiration (recommended: 6 months or 12 months)
     - Click **"Add"**
     - **COPY THE VALUE IMMEDIATELY** - it will only be shown once!

5. **Update Your .env File**
   ```bash
   AZURE_ENTRA_CLIENT_SECRET=<paste-your-secret-value-here>
   ```

---

## Method 2: Quick Navigation

Direct URL format:
```
https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Credentials/appId/e6b439ec-8ff5-43e9-b54c-90c0db989792
```

Or search path:
```
Portal → Entra ID → App registrations → EVA Suite → Certificates & secrets
```

---

## Your EVA Suite App Details

- **Display Name**: EVA Suite
- **Application (Client) ID**: `e6b439ec-8ff5-43e9-b54c-90c0db989792`
- **Object ID**: `e71d978b-7576-44e1-ae41-897ef48d6757`
- **Directory (Tenant) ID**: `bfb12ca1-7f37-47d5-9cf5-8aa52214a0d8`
- **Client Credentials**: 1 secret (according to your info)

---

## If You Need to Create a NEW Secret

1. Go to: **Entra ID → App registrations → EVA Suite → Certificates & secrets**
2. Click **"+ New client secret"**
3. Enter details:
   - **Description**: `EVA API Production Secret`
   - **Expires**: 12 months (or as per your security policy)
4. Click **"Add"**
5. **IMMEDIATELY COPY** the "Value" column (NOT the "Secret ID")
6. Paste into your `.env` file:
   ```bash
   AZURE_ENTRA_CLIENT_SECRET=your-copied-secret-value-here
   ```

---

## Security Best Practices

- ✅ Never commit secrets to Git
- ✅ Store in Azure Key Vault for production
- ✅ Rotate secrets every 6-12 months
- ✅ Use separate secrets for dev/staging/production
- ✅ Set appropriate expiration dates

---

## Verify Configuration

After updating the secret, run:
```bash
python check_azure_connectivity.py
```

Look for:
```
[Azure Entra ID]
  Client Secret: ***<last-4-chars>  # Should show last 4 characters
```

---

## Common Issues

**Problem**: "Client secret has expired"
- **Solution**: Create a new secret following the steps above

**Problem**: "Invalid client secret"
- **Solution**: Double-check you copied the **Value** (not Secret ID)

**Problem**: Can't see existing secret value
- **Reason**: Azure never shows secret values again after creation
- **Solution**: Create a new secret and use that

---

## Next Steps

Once you have the client secret:
1. Update `.env` file with the secret
2. Run `python check_azure_connectivity.py` to verify
3. Run `python test_phase1_features.py` to test JWT authentication
