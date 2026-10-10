-- CreateTable
CREATE TABLE "Font" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'draft',
    "trialFile" TEXT,
    "boothUrl" TEXT,
    "boothProductId" TEXT,
    "boothName" TEXT,
    "boothThumbnail" TEXT,
    "boothDescription" TEXT,
    "boothPrice" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Font_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Event" (
    "id" TEXT NOT NULL,
    "fontId" TEXT NOT NULL,
    "eventType" TEXT NOT NULL,
    "country" TEXT,
    "referrer" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Event_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Font_slug_key" ON "Font"("slug");

-- CreateIndex
CREATE INDEX "Event_fontId_idx" ON "Event"("fontId");

-- CreateIndex
CREATE INDEX "Event_eventType_idx" ON "Event"("eventType");

-- AddForeignKey
ALTER TABLE "Event" ADD CONSTRAINT "Event_fontId_fkey" FOREIGN KEY ("fontId") REFERENCES "Font"("id") ON DELETE CASCADE ON UPDATE CASCADE;
