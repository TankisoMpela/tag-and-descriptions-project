-- AlterTable
ALTER TABLE "Font" ADD COLUMN     "characterSet" TEXT,
ADD COLUMN     "featured" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "license" TEXT,
ADD COLUMN     "shortDescription" TEXT,
ADD COLUMN     "styles" TEXT;
