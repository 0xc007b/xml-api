<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>

    <!-- Root template -->
    <xsl:template match="/">
        <html>
            <head>
                <title>Library Catalog</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h1, h2, h3 {
                        color: #333;
                    }
                    .library-info {
                        background-color: #e8f4f8;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                    .book-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 20px;
                        margin-top: 20px;
                    }
                    .book-card {
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        padding: 15px;
                        background-color: #fafafa;
                        transition: box-shadow 0.3s;
                    }
                    .book-card:hover {
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }
                    .book-title {
                        font-weight: bold;
                        color: #2c5aa0;
                        margin-bottom: 10px;
                    }
                    .book-author {
                        color: #666;
                        font-style: italic;
                    }
                    .price {
                        font-size: 1.2em;
                        color: #27ae60;
                        font-weight: bold;
                    }
                    .out-of-stock {
                        color: #e74c3c;
                        font-weight: bold;
                    }
                    .in-stock {
                        color: #27ae60;
                        font-weight: bold;
                    }
                    .genre-tag {
                        display: inline-block;
                        background-color: #3498db;
                        color: white;
                        padding: 3px 8px;
                        border-radius: 3px;
                        font-size: 0.8em;
                        margin-top: 5px;
                    }
                    .members-section {
                        margin-top: 30px;
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    }
                    .member-card {
                        background-color: white;
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                        border-left: 4px solid #3498db;
                    }
                    .stats {
                        display: flex;
                        gap: 20px;
                        margin: 20px 0;
                    }
                    .stat-box {
                        background-color: #ecf0f1;
                        padding: 15px;
                        border-radius: 5px;
                        text-align: center;
                        flex: 1;
                    }
                    .stat-number {
                        font-size: 2em;
                        font-weight: bold;
                        color: #2c3e50;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Library Catalog</h1>

                    <!-- Library Information -->
                    <div class="library-info">
                        <h2><xsl:value-of select="library/metadata/name"/></h2>
                        <p><strong>Location:</strong> <xsl:value-of select="library/metadata/location"/></p>
                        <p><strong>Established:</strong> <xsl:value-of select="library/metadata/established"/></p>
                    </div>

                    <!-- Statistics -->
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number">
                                <xsl:value-of select="count(library/books/book)"/>
                            </div>
                            <div>Total Books</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">
                                <xsl:value-of select="count(library/books/book[availability='in-stock'])"/>
                            </div>
                            <div>Available</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">
                                <xsl:value-of select="count(library/members/member)"/>
                            </div>
                            <div>Members</div>
                        </div>
                    </div>

                    <!-- Books Section -->
                    <h2>Books Collection</h2>
                    <div class="book-grid">
                        <xsl:for-each select="library/books/book">
                            <xsl:sort select="title"/>
                            <div class="book-card">
                                <div class="book-title">
                                    <xsl:value-of select="title"/>
                                </div>
                                <div class="book-author">
                                    by <xsl:value-of select="author"/>
                                </div>
                                <p>
                                    <strong>Year:</strong> <xsl:value-of select="year"/><br/>
                                    <strong>Publisher:</strong> <xsl:value-of select="publisher"/><br/>
                                    <strong>ISBN:</strong> <xsl:value-of select="@isbn"/>
                                </p>
                                <p class="price">
                                    <xsl:value-of select="price/@currency"/>
                                    <xsl:text> </xsl:text>
                                    <xsl:value-of select="price"/>
                                </p>
                                <p>
                                    <xsl:choose>
                                        <xsl:when test="availability='in-stock'">
                                            <span class="in-stock">✓ Available</span>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <span class="out-of-stock">✗ Out of Stock</span>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </p>
                                <p><xsl:value-of select="description"/></p>
                                <span class="genre-tag"><xsl:value-of select="@genre"/></span>
                            </div>
                        </xsl:for-each>
                    </div>

                    <!-- Members Section -->
                    <div class="members-section">
                        <h2>Library Members</h2>
                        <xsl:for-each select="library/members/member">
                            <div class="member-card">
                                <h3><xsl:value-of select="name"/></h3>
                                <p>
                                    <strong>Member ID:</strong> <xsl:value-of select="@id"/><br/>
                                    <strong>Type:</strong> <xsl:value-of select="@type"/><br/>
                                    <strong>Email:</strong> <xsl:value-of select="email"/><br/>
                                    <strong>Joined:</strong> <xsl:value-of select="joined"/>
                                </p>
                                <xsl:if test="borrowed_books/book_ref">
                                    <p><strong>Currently Borrowed:</strong></p>
                                    <ul>
                                        <xsl:for-each select="borrowed_books/book_ref">
                                            <xsl:variable name="book-id" select="@id"/>
                                            <li>
                                                <xsl:value-of select="//book[@id=$book-id]/title"/>
                                                <xsl:text> by </xsl:text>
                                                <xsl:value-of select="//book[@id=$book-id]/author"/>
                                            </li>
                                        </xsl:for-each>
                                    </ul>
                                </xsl:if>
                            </div>
                        </xsl:for-each>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
