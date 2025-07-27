<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

    <!-- Root template -->
    <xsl:template match="/">
        <catalog>
            <xsl:attribute name="generated">
                <xsl:value-of select="'2024-01-01'"/>
            </xsl:attribute>

            <!-- Library information -->
            <library_info>
                <xsl:apply-templates select="library/metadata"/>
            </library_info>

            <!-- Books catalog -->
            <books>
                <xsl:attribute name="count">
                    <xsl:value-of select="count(library/books/book)"/>
                </xsl:attribute>
                <xsl:apply-templates select="library/books/book">
                    <xsl:sort select="year" data-type="number" order="descending"/>
                </xsl:apply-templates>
            </books>

            <!-- Genre summary -->
            <genres>
                <xsl:call-template name="genre-summary"/>
            </genres>

            <!-- Availability summary -->
            <availability_summary>
                <in_stock>
                    <xsl:value-of select="count(library/books/book[availability='in-stock'])"/>
                </in_stock>
                <out_of_stock>
                    <xsl:value-of select="count(library/books/book[availability='out-of-stock'])"/>
                </out_of_stock>
            </availability_summary>
        </catalog>
    </xsl:template>

    <!-- Library metadata template -->
    <xsl:template match="metadata">
        <name><xsl:value-of select="name"/></name>
        <location><xsl:value-of select="location"/></location>
        <year_established><xsl:value-of select="established"/></year_established>
    </xsl:template>

    <!-- Book template -->
    <xsl:template match="book">
        <item>
            <xsl:attribute name="id">
                <xsl:value-of select="@id"/>
            </xsl:attribute>
            <xsl:attribute name="isbn">
                <xsl:value-of select="@isbn"/>
            </xsl:attribute>
            <xsl:attribute name="category">
                <xsl:value-of select="@genre"/>
            </xsl:attribute>

            <title><xsl:value-of select="title"/></title>
            <creator><xsl:value-of select="author"/></creator>
            <publication_year><xsl:value-of select="year"/></publication_year>
            <publishing_house><xsl:value-of select="publisher"/></publishing_house>

            <pricing>
                <xsl:attribute name="currency">
                    <xsl:value-of select="price/@currency"/>
                </xsl:attribute>
                <amount><xsl:value-of select="price"/></amount>
            </pricing>

            <status>
                <xsl:choose>
                    <xsl:when test="availability='in-stock'">
                        <xsl:text>Available</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>Unavailable</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </status>

            <summary>
                <xsl:value-of select="description"/>
            </summary>

            <!-- Check if borrowed -->
            <xsl:if test="//member/borrowed_books/book_ref[@id=current()/@id]">
                <borrowed_by>
                    <xsl:for-each select="//member[borrowed_books/book_ref[@id=current()/@id]]">
                        <member>
                            <xsl:attribute name="id">
                                <xsl:value-of select="@id"/>
                            </xsl:attribute>
                            <xsl:value-of select="name"/>
                        </member>
                    </xsl:for-each>
                </borrowed_by>
            </xsl:if>
        </item>
    </xsl:template>

    <!-- Genre summary template -->
    <xsl:template name="genre-summary">
        <xsl:for-each select="//book[not(@genre=preceding::book/@genre)]">
            <xsl:variable name="current-genre" select="@genre"/>
            <genre>
                <xsl:attribute name="type">
                    <xsl:value-of select="$current-genre"/>
                </xsl:attribute>
                <xsl:attribute name="count">
                    <xsl:value-of select="count(//book[@genre=$current-genre])"/>
                </xsl:attribute>
                <books>
                    <xsl:for-each select="//book[@genre=$current-genre]">
                        <book_ref>
                            <xsl:attribute name="id">
                                <xsl:value-of select="@id"/>
                            </xsl:attribute>
                            <xsl:value-of select="title"/>
                        </book_ref>
                    </xsl:for-each>
                </books>
            </genre>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>
