import type { Product } from "@/lib/types";

export type CatalogItem = Product & { id: string };

export const CATALOG: CatalogItem[] = [
  { id: "bag", name: "Leather Bag", price: "89", image: "/products/leather-bag.svg" },
  { id: "sneaker", name: "Blue Sneaker", price: "120", image: "/products/blue-sneaker.svg" },
  { id: "mug", name: "Ceramic Mug", price: "24", image: "/products/ceramic-mug.svg" },
  { id: "scarf", name: "Wool Scarf", price: "45", image: "/products/wool-scarf.svg" },
  { id: "lamp", name: "Brass Lamp", price: "76", image: "/products/brass-lamp.svg" },
  { id: "shirt", name: "Linen Shirt", price: "58", image: "/products/linen-shirt.svg" },
];
