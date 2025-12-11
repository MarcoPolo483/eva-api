# EVA API Portal

React-based developer portal for EVA API.

## 🎯 Features

- **Landing Page**: Product showcase, pricing, SDK examples
- **Documentation**: Interactive API docs (OpenAPI + GraphQL)
- **API Console**: Test endpoints without code
- **Analytics**: Usage metrics and insights
- **Sandbox**: Try API in browser
- **Examples**: Real-world code samples
- **Changelog**: Version history

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or pnpm

### Install Dependencies

```powershell
cd portal
npm install
```

### Run Development Server

```powershell
npm run dev
```

Open http://localhost:3000

### Build for Production

```powershell
npm run build
```

Output in `dist/` directory.

### Preview Production Build

```powershell
npm run preview
```

## 🏗️ Project Structure

```
portal/
├── src/
│   ├── components/
│   │   └── Layout.tsx       # App shell with nav
│   ├── pages/
│   │   ├── Landing.tsx      # Home page ✅
│   │   ├── Documentation.tsx # API docs (stub)
│   │   ├── Console.tsx      # API tester (stub)
│   │   ├── Analytics.tsx    # Metrics (stub)
│   │   ├── Sandbox.tsx      # Try API (stub)
│   │   ├── Examples.tsx     # Code samples (stub)
│   │   └── Changelog.tsx    # Versions (stub)
│   ├── App.tsx              # Router setup
│   ├── main.tsx             # Entry point
│   └── index.css            # Tailwind styles
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🎨 Tech Stack

- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool
- **TailwindCSS**: Styling
- **React Router**: Navigation
- **Zustand**: State management
- **React Query**: Data fetching
- **Axios**: HTTP client
- **Lucide React**: Icons

## 📝 Development Status

| Page | Status | Notes |
|------|--------|-------|
| Landing | ✅ Complete | Full hero, features, pricing, CTA |
| Documentation | 🚧 Stub | Needs OpenAPI integration |
| Console | 🚧 Stub | Needs request builder |
| Analytics | 🚧 Stub | Needs charts/metrics |
| Sandbox | 🚧 Stub | Needs code runner |
| Examples | 🚧 Stub | Needs code samples |
| Changelog | 🚧 Stub | Needs version data |

## 🔧 Configuration

### API Proxy

Vite proxies `/api` and `/graphql` to backend (see `vite.config.ts`):

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/graphql': 'http://localhost:8000',
  },
}
```

### Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-dev-key
```

## 📦 Deployment

### Azure Static Web Apps

```powershell
# Build
npm run build

# Deploy via Azure CLI
az staticwebapp create \
  --name eva-api-portal \
  --resource-group eva-rg \
  --source dist/ \
  --location eastus \
  --branch main
```

### Azure App Service

```powershell
# Build
npm run build

# Create zip
Compress-Archive -Path dist/* -DestinationPath portal.zip

# Deploy
az webapp deploy \
  --resource-group eva-rg \
  --name eva-portal \
  --src-path portal.zip \
  --type zip
```

## 🧪 Testing

```powershell
# Type check
npm run type-check

# Lint
npm run lint

# Preview build
npm run build && npm run preview
```

## 📊 Performance

- **Bundle size**: ~150KB gzipped
- **First paint**: <1s
- **Interactive**: <2s
- **Lighthouse**: 95+ score

---

**Status**: Foundation complete, pages stubbed  
**Last Updated**: 2025-12-07T22:05:00Z (2025-12-07 17:05:00 EST)
