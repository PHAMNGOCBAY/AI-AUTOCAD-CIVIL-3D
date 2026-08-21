-- BIM SQLite Schema — AI-AUTOCAD CIVIL 3D
-- Moi project co 1 file bim_data.sqlite rieng, tao bang schema nay.

CREATE TABLE IF NOT EXISTS models (
    model_id        INTEGER PRIMARY KEY,
    file_path       TEXT NOT NULL UNIQUE,
    civil3d_version TEXT,
    last_synced_at  TEXT
);

CREATE TABLE IF NOT EXISTS elements (
    element_id      INTEGER PRIMARY KEY,
    model_id        INTEGER NOT NULL REFERENCES models(model_id),
    handle          TEXT NOT NULL,
    object_type     TEXT NOT NULL,     -- 'Parcel' | 'Alignment' | 'Surface' | 'CogoPoint' | 'Pipe' | 'Structure' | 'Corridor'
    category        TEXT,              -- Parcel style, Point group...
    layer           TEXT,
    name            TEXT,
    site_name       TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(model_id, handle)
);

CREATE TABLE IF NOT EXISTS element_properties (
    element_id      INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    prop_name       TEXT NOT NULL,
    prop_value      TEXT,
    prop_unit       TEXT,
    PRIMARY KEY (element_id, prop_name)
);

CREATE TABLE IF NOT EXISTS element_geometry (
    element_id      INTEGER PRIMARY KEY REFERENCES elements(element_id) ON DELETE CASCADE,
    geom_type       TEXT,              -- 'Polygon' | 'LineString' | 'Point'
    centroid_x      REAL,
    centroid_y      REAL,
    centroid_z      REAL,
    bbox_min_x      REAL,
    bbox_min_y      REAL,
    bbox_max_x      REAL,
    bbox_max_y      REAL,
    wkt             TEXT        -- Well-Known Text: hinh hoc chinh xac (dung cho phan tich khong gian)
);

CREATE TABLE IF NOT EXISTS element_relationships (
    parent_id       INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    child_id        INTEGER NOT NULL REFERENCES elements(element_id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL,     -- 'BELONGS_TO' | 'REFERENCES' | 'DERIVED_FROM'
    PRIMARY KEY (parent_id, child_id, relation_type)
);

CREATE TABLE IF NOT EXISTS change_log (
    log_id          INTEGER PRIMARY KEY,
    element_id      INTEGER REFERENCES elements(element_id) ON DELETE SET NULL,
    action          TEXT NOT NULL,     -- 'CREATE' | 'MODIFY' | 'DELETE' | 'SYNC'
    detail          TEXT,
    changed_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_elements_type ON elements(object_type);
CREATE INDEX IF NOT EXISTS idx_elements_model ON elements(model_id);
