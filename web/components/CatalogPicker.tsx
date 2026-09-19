import { CATALOG, type CatalogItem } from "@/lib/catalog";
import { formatPrice } from "@/lib/types";

type Props = {
  tone: "a" | "b";
  selected?: Pick<CatalogItem, "name" | "image"> | null;
  onPick: (item: CatalogItem) => void;
};

export function CatalogPicker({ tone, selected, onPick }: Props) {
  return (
    <div className={`picker picker-${tone}`}>
      <p className="picker-label">Choose a product</p>
      <div className="picker-grid">
        {CATALOG.map((item) => {
          const active = selected?.image === item.image || selected?.name === item.name;
          return (
            <button
              key={item.id}
              type="button"
              className={active ? "on" : ""}
              onClick={() => onPick(item)}
            >
              <img src={item.image} alt="" />
              <span>
                <strong>{item.name}</strong>
                {formatPrice(item.price)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
