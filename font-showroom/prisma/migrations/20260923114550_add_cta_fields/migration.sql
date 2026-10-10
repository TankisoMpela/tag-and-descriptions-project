-- AlterTable
ALTER TABLE "Font" ADD COLUMN     "ctaButton" TEXT,
ADD COLUMN     "ctaHeadline" TEXT,
ADD COLUMN     "ctaMessage" TEXT,
ADD COLUMN     "ctaVariant" TEXT NOT NULL DEFAULT 'shop_growth';
