-- AlterTable
ALTER TABLE "Event" ADD COLUMN     "variant" TEXT;

-- AlterTable
ALTER TABLE "Font" ALTER COLUMN "ctaVariant" SET DEFAULT 'ab';

-- CreateIndex
CREATE INDEX "Event_variant_idx" ON "Event"("variant");
