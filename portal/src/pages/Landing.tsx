import { Link } from 'react-router-dom'
import { ArrowRight, Zap, Shield, Code, BarChart, Check } from 'lucide-react'

export default function Landing() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-primary-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Enterprise AI Platform API
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Build intelligent document management and query systems with EVA's powerful REST and GraphQL APIs. 
            Azure-native, enterprise-ready, and battle-tested.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/docs" className="btn-primary text-lg px-8 py-3">
              Get Started
              <ArrowRight className="inline-block ml-2 h-5 w-5" />
            </Link>
            <Link to="/sandbox" className="btn-secondary text-lg px-8 py-3">
              Try Sandbox
            </Link>
          </div>
          
          {/* Quick Stats */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <div className="text-4xl font-bold text-primary-600">99.9%</div>
              <div className="text-gray-600 mt-2">Uptime SLA</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600">&lt;200ms</div>
              <div className="text-gray-600 mt-2">Avg Response</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600">17</div>
              <div className="text-gray-600 mt-2">API Endpoints</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-primary-600">3</div>
              <div className="text-gray-600 mt-2">SDK Languages</div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Everything you need to build AI-powered applications
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="card">
              <Zap className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
              <p className="text-gray-600">
                Built on FastAPI and Azure Cosmos DB for sub-200ms response times. Async throughout.
              </p>
            </div>
            
            <div className="card">
              <Shield className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
              <p className="text-gray-600">
                Azure AD B2C integration, JWT authentication, rate limiting, and comprehensive audit logs.
              </p>
            </div>
            
            <div className="card">
              <Code className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">GraphQL + REST</h3>
              <p className="text-gray-600">
                Choose your preferred API style. Full OpenAPI spec and GraphQL schema with subscriptions.
              </p>
            </div>
            
            <div className="card">
              <BarChart className="h-12 w-12 text-primary-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Built-in Analytics</h3>
              <p className="text-gray-600">
                Real-time usage metrics, performance monitoring, and Azure Application Insights integration.
              </p>
            </div>
            
            <div className="card">
              <svg className="h-12 w-12 text-primary-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-xl font-semibold mb-2">Document Management</h3>
              <p className="text-gray-600">
                Upload, process, and query documents with Azure Blob Storage and AI-powered search.
              </p>
            </div>
            
            <div className="card">
              <svg className="h-12 w-12 text-primary-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <h3 className="text-xl font-semibold mb-2">RAG Queries</h3>
              <p className="text-gray-600">
                Retrieval-augmented generation with Azure OpenAI for intelligent document Q&A.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* SDK Section */}
      <section className="bg-gray-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Official SDKs for Every Platform
            </h2>
            <p className="text-xl text-gray-600">
              Auto-generated from OpenAPI spec. Always up-to-date.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card">
              <h3 className="text-2xl font-bold mb-4">Python</h3>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
{`pip install eva-api-sdk

from eva_api import Client

client = Client(api_key="your-key")
spaces = client.spaces.list()`}
              </pre>
            </div>
            
            <div className="card">
              <h3 className="text-2xl font-bold mb-4">TypeScript</h3>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
{`npm install @eva/api-sdk

import { EvaClient } from '@eva/api-sdk'

const client = new EvaClient('your-key')
const spaces = await client.spaces.list()`}
              </pre>
            </div>
            
            <div className="card">
              <h3 className="text-2xl font-bold mb-4">.NET</h3>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
{`dotnet add package Eva.Api.Sdk

using Eva.Api;

var client = new EvaClient("your-key");
var spaces = await client.Spaces.ListAsync();`}
              </pre>
            </div>
          </div>
        </div>
      </section>
      
      {/* Pricing Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600">
              Pay for what you use. No hidden fees.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card border-2 border-gray-200">
              <h3 className="text-2xl font-bold mb-4">Free</h3>
              <div className="text-4xl font-bold text-primary-600 mb-6">$0<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>1,000 API calls/month</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>1GB document storage</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Basic support</span>
                </li>
              </ul>
              <button className="btn-secondary w-full">Get Started</button>
            </div>
            
            <div className="card border-2 border-primary-600 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                Popular
              </div>
              <h3 className="text-2xl font-bold mb-4">Pro</h3>
              <div className="text-4xl font-bold text-primary-600 mb-6">$99<span className="text-lg text-gray-600">/mo</span></div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>100,000 API calls/month</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>100GB document storage</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Priority support</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Advanced analytics</span>
                </li>
              </ul>
              <button className="btn-primary w-full">Start Free Trial</button>
            </div>
            
            <div className="card border-2 border-gray-200">
              <h3 className="text-2xl font-bold mb-4">Enterprise</h3>
              <div className="text-4xl font-bold text-primary-600 mb-6">Custom</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Unlimited API calls</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Unlimited storage</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>24/7 dedicated support</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>Custom SLA</span>
                </li>
                <li className="flex items-start">
                  <Check className="h-5 w-5 text-green-500 mr-2 mt-0.5" />
                  <span>On-premise deployment</span>
                </li>
              </ul>
              <button className="btn-secondary w-full">Contact Sales</button>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="bg-primary-600 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to build with EVA?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Get your API key and start building in minutes
          </p>
          <Link to="/docs" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block">
            Read the Docs
            <ArrowRight className="inline-block ml-2 h-5 w-5" />
          </Link>
        </div>
      </section>
    </div>
  )
}
