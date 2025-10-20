"""GraphQL эндпоинты"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from starlette.graphql import GraphQLApp
from graphene import Schema
import logging

from app.api.graphql.schema import schema
from app.api.deps import get_current_user_optional
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/graphql", response_class=HTMLResponse)
async def graphql_playground():
    """GraphQL Playground для тестирования запросов"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Universal Parser GraphQL Playground</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/css/index.css" />
        <link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/favicon.png" />
        <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/js/middleware.js"></script>
    </head>
    <body>
        <div id="root">
            <style>
                body {
                    margin: 0;
                    background: #172a3a;
                    font-family: 'Open Sans', sans-serif;
                    overflow: hidden;
                }
                #root {
                    width: 100vw;
                    height: 100vh;
                }
            </style>
            <div style="display: flex; align-items: center; justify-content: center; height: 100vh; color: white; font-size  # noqa  # noqa: E501 E501 24px;">
                Loading GraphQL Playground...
            </div>
        </div>
        <script>
            window.addEventListener('load', function (event) {
                GraphQLPlayground.init(document.getElementById('root'), {
                    endpoint: '/api/v1/graphql',
                    settings: {
                        'request.credentials': 'include',
                        'editor.theme': 'dark',
                        'editor.fontSize': 14,
                        'editor.fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                        'editor.cursorShape': 'line',
                        'editor.reuseHeaders': true,
                        'tracing.hideTracingResponse': false,
                        'queryPlan.hideQueryPlanResponse': false,
                        'editor.fontSize': 14,
                        'editor.fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                        'editor.cursorShape': 'line',
                        'editor.reuseHeaders': true,
                        'tracing.hideTracingResponse': false,
                        'queryPlan.hideQueryPlanResponse': false,
                        'editor.fontSize': 14,
                        'editor.fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                        'editor.cursorShape': 'line',
                        'editor.reuseHeaders': true,
                        'tracing.hideTracingResponse': false,
                        'queryPlan.hideQueryPlanResponse': false
                    },
                    tabs: [
                        {
                            endpoint: '/api/v1/graphql',
                            query: `# Welcome to Universal Parser GraphQL API
# 
# This playground allows you to explore and test GraphQL queries
# for the Universal Parser marketplace monitoring platform.
#
# Example queries:

# Get all items
query GetItems {
  items(first: 10) {
    edges {
      node {
        id
        name
        marketplace
        category
        price
        url
        createdAt
      }
    }
  }
}

# Get items by marketplace
query GetItemsByMarketplace {
  itemsByMarketplace(marketplace: "wildberries") {
    id
    name
    price
    category
  }
}

# Search items
query SearchItems {
  searchItems(query: "iPhone") {
    id
    name
    price
    marketplace
  }
}

# Get analytics overview
query GetAnalytics {
  analyticsOverview {
    totalItems
    totalUsers
    totalPosts
    totalRevenue
    activeUsers
    priceChangesToday
    newItemsToday
    topMarketplace
    topCategory
  }
}

# Get marketplace statistics
query GetMarketplaceStats {
  marketplaceStats {
    marketplace
    itemsCount
    averagePrice
    priceChanges
    newItems
    topCategory
  }
}

# Get price trends
query GetPriceTrends {
  priceTrends(marketplace: "wildberries", days: 30) {
    id
    price
    timestamp
    item {
      id
      name
    }
  }
}

# Get social posts
query GetSocialPosts {
  socialPosts(first: 10) {
    edges {
      node {
        id
        content
        author {
          id
          username
        }
        likesCount
        commentsCount
        timeAgo
        createdAt
      }
    }
  }
}

# Get user information
query GetUser {
  user(id: "user-id") {
    id
    username
    email
    itemsCount
    postsCount
    profile {
      id
      experiencePoints
      level
    }
  }
}

# Mutations

# Create item
mutation CreateItem {
  createItem(input: {
    name: "Test Item"
    marketplace: "wildberries"
    category: "electronics"
    price: 1000.0
    url: "https://example.com"
    description: "Test item description"
  }) {
    id
    name
    price
    marketplace
  }
}

# Update item
mutation UpdateItem {
  updateItem(id: "item-id", input: {
    name: "Updated Item Name"
    price: 1200.0
  }) {
    id
    name
    price
  }
}

# Delete item
mutation DeleteItem {
  deleteItem(id: "item-id")
}

# Create social post
mutation CreateSocialPost {
  createSocialPost(input: {
    content: "This is a test post"
    authorId: "user-id"
    itemId: "item-id"
  }) {
    id
    content
    author {
      id
      username
    }
  }
}

# Like post
mutation LikePost {
  likePost(id: "post-id")
}

# Unlike post
mutation UnlikePost {
  unlikePost(id: "post-id")
}

# Subscriptions (WebSocket)

# Subscribe to item updates
subscription ItemUpdated {
  itemUpdated(itemId: "item-id") {
    id
    name
    price
    updatedAt
  }
}

# Subscribe to price changes
subscription PriceChanged {
  priceChanged(itemId: "item-id") {
    id
    price
    timestamp
    item {
      id
      name
    }
  }
}

# Subscribe to new social posts
subscription NewSocialPost {
  newSocialPost {
    id
    content
    author {
      id
      username
    }
    createdAt
  }
}
`
                        }
                    ]
                });
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/graphql/schema")
async def graphql_schema():
    """Получить GraphQL схему в формате SDL"""
    try:
        # В реальном приложении здесь был бы экспорт схемы в SDL формате
        sdl_schema = """
        type Query {
            items(first: Int, after: String, last: Int, before: String): ItemConnection
            item(id: ID!): Item
            itemsByMarketplace(marketplace: String!): [Item]
            itemsByCategory(category: String!): [Item]
            searchItems(query: String!): [Item]
            users(first: Int, after: String, last: Int, before: String): UserConnection
            user(id: ID!): User
            userByUsername(username: String!): User
            socialPosts(first: Int, after: String, last: Int, before: String): SocialPostConnection
            socialPost(id: ID!): SocialPost
            userPosts(userId: ID!): [SocialPost]
            priceHistory(itemId: ID!): [PriceHistory]
            priceTrends(marketplace: String, category: String, days: Int): [PriceHistory]
            analyticsOverview: AnalyticsOverview
            marketplaceStats: [MarketplaceStats]
            categoryStats: [CategoryStats]
        }

        type Mutation {
            createItem(input: CreateItemInput!): Item
            updateItem(id: ID!, input: UpdateItemInput!): Item
            deleteItem(id: ID!): Boolean
            createSocialPost(input: CreateSocialPostInput!): SocialPost
            likePost(id: ID!): Boolean
            unlikePost(id: ID!): Boolean
        }

        type Subscription {
            itemUpdated(itemId: ID!): Item
            priceChanged(itemId: ID!): PriceHistory
            newSocialPost(userId: ID): SocialPost
        }

        type Item {
            id: ID!
            name: String!
            marketplace: String!
            category: String
            price: Float
            url: String
            description: String
            imageUrl: String
            createdAt: DateTime
            updatedAt: DateTime
            currentPrice: Float
            priceChangePercent: Float
            marketplaceDisplayName: String
            categoryDisplayName: String
        }

        type User {
            id: ID!
            username: String!
            email: String!
            isActive: Boolean
            createdAt: DateTime
            updatedAt: DateTime
            profile: UserProfile
            itemsCount: Int
            postsCount: Int
        }

        type UserProfile {
            id: ID!
            experiencePoints: Int
            level: Int
            bio: String
            avatar: String
            createdAt: DateTime
            updatedAt: DateTime
        }

        type PriceHistory {
            id: ID!
            itemId: ID!
            price: Float!
            timestamp: DateTime!
            item: Item
            priceChange: Float
            formattedPrice: String
        }

        type SocialPost {
            id: ID!
            content: String!
            authorId: ID!
            itemId: ID
            mediaUrls: [String]
            createdAt: DateTime
            updatedAt: DateTime
            author: User
            likesCount: Int
            commentsCount: Int
            timeAgo: String
        }

        type AnalyticsOverview {
            totalItems: Int
            totalUsers: Int
            totalPosts: Int
            totalRevenue: Float
            activeUsers: Int
            priceChangesToday: Int
            newItemsToday: Int
            topMarketplace: String
            topCategory: String
        }

        type MarketplaceStats {
            marketplace: String
            itemsCount: Int
            averagePrice: Float
            priceChanges: Int
            newItems: Int
            topCategory: String
        }

        type CategoryStats {
            category: String
            itemsCount: Int
            averagePrice: Float
            priceChanges: Int
            newItems: Int
            topMarketplace: String
        }

        input CreateItemInput {
            name: String!
            marketplace: String!
            category: String
            price: Float
            url: String
            description: String
            imageUrl: String
        }

        input UpdateItemInput {
            name: String
            category: String
            price: Float
            description: String
            imageUrl: String
        }

        input CreateSocialPostInput {
            content: String!
            authorId: ID!
            itemId: ID
            mediaUrls: [String]
        }

        scalar DateTime
        """

        return {"schema": sdl_schema}

    except Exception as e:
        logger.error("Error getting GraphQL schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting GraphQL schema: {e}"
        )

@router.get("/graphql/introspection")
async def graphql_introspection():
    """Получить GraphQL introspection данные"""
    try:
        # В реальном приложении здесь был бы introspection запрос
        introspection_data = {
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": {"name": "Mutation"},
                    "subscriptionType": {"name": "Subscription"},
                    "types": [
                        {
                            "name": "Query",
                            "kind": "OBJECT",
                            "fields": [
                                {
                                    "name": "items",
                                    "type": {"name": "ItemConnection", "kind": "OBJECT"}
                                },
                                {
                                    "name": "item",
                                    "type": {"name": "Item", "kind": "OBJECT"}
                                }
                            ]
                        }
                    ]
                }
            }
        }

        return introspection_data

    except Exception as e:
        logger.error("Error getting GraphQL introspection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting GraphQL introspection: {e}"
        )

@router.get("/graphql/health")
async def graphql_health():
    """Проверить состояние GraphQL API"""
    try:
        # В реальном приложении здесь была бы проверка состояния
        return {
            "status": "healthy",
            "message": "GraphQL API is running",
            "version": "1.0.0",
            "features": [
                "Query",
                "Mutation", 
                "Subscription",
                "Real-time updates",
                "WebSocket support",
                "Introspection",
                "Playground"
            ]
        }

    except Exception as e:
        logger.error("Error checking GraphQL health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking GraphQL health: {e}"
        )

# Создаем GraphQL приложение
graphql_app = GraphQLApp(schema=schema, graphiql=True)

@router.get("/graphql/endpoint")
async def graphql_endpoint():
    """Основной GraphQL эндпоинт"""
    return {"message": "GraphQL endpoint is available at /api/v1/graphql"}

# Добавляем GraphQL приложение к роутеру
router.add_route("/graphql", graphql_app, methods=["GET", "POST"])
